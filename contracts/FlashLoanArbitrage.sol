// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@balancer-labs/v2-interfaces/contracts/vault/IVault.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./FlashLoanRiskAnalyzer.sol";

interface IMoonwell {
    function supply(address asset, uint256 amount) external returns (bool);
    function borrow(address asset, uint256 amount) external returns (bool);
    function getAccountLiquidity(address account) external view returns (uint256, uint256, uint256);
}

contract FlashLoanArbitrage is Ownable {
    IVault private immutable balancerVault;
    FlashLoanRiskAnalyzer public riskAnalyzer;
    IMoonwell public moonwell;
    IERC20 public usdc;
    
    uint256 public constant RISK_THRESHOLD = 80;
    uint256 public constant LEVERAGE_RATIO = 3;
    
    event YieldPositionOpened(address user, uint256 depositAmount, uint256 leveragedAmount);
    event YieldPositionClosed(address user, uint256 withdrawAmount, uint256 profit);
    
    constructor(
        address _balancerVault,
        address _riskAnalyzer,
        address _moonwell,
        address _usdc
    ) {
        balancerVault = IVault(_balancerVault);
        riskAnalyzer = FlashLoanRiskAnalyzer(_riskAnalyzer);
        moonwell = IMoonwell(_moonwell);
        usdc = IERC20(_usdc);
    }
    
    function executeYieldStrategy(
        uint256 depositAmount,
        bytes calldata params
    ) external onlyOwner {
        // Check risk first
        uint256 riskScore = riskAnalyzer.assessContractRisk(
            address(this),
            _getInvolvedTokens(address(usdc)),
            new address[](0)  // No DEXes involved in yield farming
        );
        
        require(riskScore < RISK_THRESHOLD, "Risk too high");
        
        // Calculate flash loan amount for 3x leverage
        uint256 flashLoanAmount = depositAmount * 2;  // 2x to achieve 3x total
        
        // Request flash loan from Balancer
        IERC20[] memory tokens = new IERC20[](1);
        tokens[0] = usdc;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = flashLoanAmount;
        
        // Execute flash loan
        balancerVault.flashLoan(
            address(this),
            tokens,
            amounts,
            params
        );
    }
    
    function receiveFlashLoan(
        IERC20[] memory tokens,
        uint256[] memory amounts,
        uint256[] memory feeAmounts,
        bytes memory userData
    ) external {
        require(msg.sender == address(balancerVault), "Only Balancer Vault");
        
        // Get user deposit amount from userData
        uint256 userDeposit = abi.decode(userData, (uint256));
        uint256 totalAmount = userDeposit + amounts[0];
        
        // 1. Supply total amount to Moonwell
        usdc.approve(address(moonwell), totalAmount);
        require(moonwell.supply(address(usdc), totalAmount), "Supply failed");
        
        // 2. Borrow amount needed to repay flash loan
        require(moonwell.borrow(address(usdc), amounts[0]), "Borrow failed");
        
        // 3. Approve and repay flash loan
        usdc.approve(address(balancerVault), amounts[0]);
        
        // Check health factor after leverage
        (,, uint256 healthFactor) = moonwell.getAccountLiquidity(address(this));
        require(healthFactor >= 150, "Health factor too low"); // 1.5 minimum
        
        emit YieldPositionOpened(owner(), userDeposit, totalAmount);
    }
    
    function _getInvolvedTokens(address baseToken) internal pure returns (address[] memory) {
        // In a real implementation, this would return all tokens involved in the trade path
        address[] memory tokens = new address[](1);
        tokens[0] = baseToken;
        return tokens;
    }
    
    function withdrawToken(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No balance to withdraw");
        IERC20(token).transfer(owner(), balance);
    }
}
