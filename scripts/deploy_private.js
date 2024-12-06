require('dotenv').config({ path: '.env.private' });
const hre = require("hardhat");

async function main() {
  console.log('Deploying contracts privately...');
  
  // Get deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log('Deploying from account:', deployer.address);
  
  // Deploy Risk Analyzer first
  const FlashLoanRiskAnalyzer = await hre.ethers.getContractFactory("FlashLoanRiskAnalyzer");
  const riskAnalyzer = await FlashLoanRiskAnalyzer.deploy();
  await riskAnalyzer.deployed();
  console.log('FlashLoanRiskAnalyzer deployed to:', riskAnalyzer.address);
  
  // Deploy Flash Loan contract
  const FlashLoanArbitrage = await hre.ethers.getContractFactory("FlashLoanArbitrage");
  const flashLoan = await FlashLoanArbitrage.deploy(
    process.env.BALANCER_VAULT,  // Balancer Vault address
    riskAnalyzer.address
  );
  await flashLoan.deployed();
  console.log('FlashLoanArbitrage deployed to:', flashLoan.address);
  
  // Verify contracts if on a supported network (optional)
  if (hre.network.name !== "hardhat") {
    try {
      await hre.run("verify:verify", {
        address: riskAnalyzer.address,
        constructorArguments: [],
      });
      
      await hre.run("verify:verify", {
        address: flashLoan.address,
        constructorArguments: [process.env.BALANCER_VAULT, riskAnalyzer.address],
      });
    } catch (error) {
      console.log('Error verifying contracts:', error);
    }
  }
  
  // Save deployed addresses to a private file
  const fs = require('fs');
  const deployments = {
    riskAnalyzer: riskAnalyzer.address,
    flashLoan: flashLoan.address,
    timestamp: new Date().toISOString(),
    network: hre.network.name
  };
  
  fs.writeFileSync(
    'deployments.private.json',
    JSON.stringify(deployments, null, 2)
  );
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
