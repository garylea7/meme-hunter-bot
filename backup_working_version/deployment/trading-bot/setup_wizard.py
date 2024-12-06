import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import json
import os
import requests
from pathlib import Path

class SetupWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flash Trading Bot Setup Wizard")
        self.root.geometry("800x600")
        
        # Config file path
        self.config_path = Path("config/setup_config.json")
        self.config = self.load_config()
        
        # Style
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("Step.TLabel", font=("Arial", 10))
        
        self.create_gui()
        
    def load_config(self):
        """Load or create config file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "wallet": {"address": "", "network": "devnet"},
            "rpc": {
                "quicknode": "",
                "helius": "",
                "backup": ""
            },
            "apis": {
                "goplus": "",
                "birdeye": ""
            },
            "setup_complete": False
        }
    
    def save_config(self):
        """Save config to file"""
        self.config_path.parent.mkdir(exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def create_gui(self):
        # Main container
        main = ttk.Frame(self.root, padding="10")
        main.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        ttk.Label(main, text="Flash Trading Bot Setup", style="Header.TLabel").grid(row=0, column=0, pady=20)
        
        # Steps Frame
        steps = ttk.LabelFrame(main, text="Setup Steps", padding="10")
        steps.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Step 1: Phantom Wallet
        self.wallet_var = tk.StringVar(value="❌")
        ttk.Label(steps, text="1. Phantom Wallet Setup", style="Step.TLabel").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(steps, textvariable=self.wallet_var).grid(row=0, column=1, padx=5)
        ttk.Button(steps, text="Setup", command=self.setup_wallet).grid(row=0, column=2)
        
        # Step 2: RPC Setup
        self.rpc_var = tk.StringVar(value="❌")
        ttk.Label(steps, text="2. RPC Endpoint Setup", style="Step.TLabel").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(steps, textvariable=self.rpc_var).grid(row=1, column=1, padx=5)
        ttk.Button(steps, text="Setup", command=self.setup_rpc).grid(row=1, column=2)
        
        # Step 3: API Setup
        self.api_var = tk.StringVar(value="❌")
        ttk.Label(steps, text="3. API Keys Setup", style="Step.TLabel").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(steps, textvariable=self.api_var).grid(row=2, column=1, padx=5)
        ttk.Button(steps, text="Setup", command=self.setup_apis).grid(row=2, column=2)
        
        # Configuration Display
        config_frame = ttk.LabelFrame(main, text="Current Configuration", padding="10")
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.config_text = tk.Text(config_frame, height=10, width=70)
        self.config_text.grid(row=0, column=0, pady=5)
        self.update_config_display()
        
        # Buttons
        button_frame = ttk.Frame(main)
        button_frame.grid(row=3, column=0, pady=20)
        
        ttk.Button(button_frame, text="Verify Setup", command=self.verify_setup).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save", command=self.save_and_exit).grid(row=0, column=1, padx=5)
        
    def setup_wallet(self):
        wallet_window = tk.Toplevel(self.root)
        wallet_window.title("Phantom Wallet Setup")
        wallet_window.geometry("600x400")
        
        frame = ttk.Frame(wallet_window, padding="10")
        frame.grid(row=0, column=0)
        
        # Instructions
        instructions = [
            "1. Install Phantom Wallet Chrome extension if not already installed",
            "2. Create a new wallet named 'Flash_Test'",
            "3. Save the seed phrase securely",
            "4. Switch to Devnet in Developer Settings",
            "5. Copy your wallet address below"
        ]
        
        for i, text in enumerate(instructions):
            ttk.Label(frame, text=text).grid(row=i, column=0, pady=5, sticky=tk.W)
        
        # Wallet address entry
        ttk.Label(frame, text="Wallet Address:").grid(row=len(instructions), column=0, pady=10)
        address_entry = ttk.Entry(frame, width=50)
        address_entry.grid(row=len(instructions)+1, column=0, pady=5)
        
        def install_phantom():
            webbrowser.open("https://phantom.app")
        
        def save_wallet():
            address = address_entry.get().strip()
            if len(address) < 32:
                messagebox.showerror("Error", "Please enter a valid Solana wallet address")
                return
            self.config["wallet"]["address"] = address
            self.wallet_var.set("✅")
            self.update_config_display()
            wallet_window.destroy()
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(instructions)+2, column=0, pady=20)
        
        ttk.Button(button_frame, text="Install Phantom", command=install_phantom).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save", command=save_wallet).grid(row=0, column=1, padx=5)
    
    def setup_rpc(self):
        rpc_window = tk.Toplevel(self.root)
        rpc_window.title("RPC Setup")
        rpc_window.geometry("600x400")
        
        frame = ttk.Frame(rpc_window, padding="10")
        frame.grid(row=0, column=0)
        
        # Instructions
        ttk.Label(frame, text="RPC Endpoint Setup", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        
        # QuickNode
        ttk.Label(frame, text="QuickNode RPC URL:").grid(row=1, column=0, pady=5)
        quicknode_entry = ttk.Entry(frame, width=50)
        quicknode_entry.grid(row=1, column=1, pady=5)
        
        # Helius
        ttk.Label(frame, text="Helius RPC URL:").grid(row=2, column=0, pady=5)
        helius_entry = ttk.Entry(frame, width=50)
        helius_entry.grid(row=2, column=1, pady=5)
        
        def open_quicknode():
            webbrowser.open("https://www.quicknode.com/signup")
            
        def open_helius():
            webbrowser.open("https://dev.helius.xyz/dashboard/app")
        
        def save_rpc():
            quicknode = quicknode_entry.get().strip()
            helius = helius_entry.get().strip()
            
            if not (quicknode or helius):
                messagebox.showerror("Error", "Please enter at least one RPC endpoint")
                return
                
            self.config["rpc"]["quicknode"] = quicknode
            self.config["rpc"]["helius"] = helius
            self.rpc_var.set("✅")
            self.update_config_display()
            rpc_window.destroy()
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="QuickNode Signup", command=open_quicknode).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Helius Signup", command=open_helius).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Save", command=save_rpc).grid(row=0, column=2, padx=5)
    
    def setup_apis(self):
        api_window = tk.Toplevel(self.root)
        api_window.title("API Setup")
        api_window.geometry("600x400")
        
        frame = ttk.Frame(api_window, padding="10")
        frame.grid(row=0, column=0)
        
        # Instructions
        ttk.Label(frame, text="API Keys Setup", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        
        # GoPlus
        ttk.Label(frame, text="GoPlus API Key:").grid(row=1, column=0, pady=5)
        goplus_entry = ttk.Entry(frame, width=50)
        goplus_entry.grid(row=1, column=1, pady=5)
        
        # Birdeye
        ttk.Label(frame, text="Birdeye API Key:").grid(row=2, column=0, pady=5)
        birdeye_entry = ttk.Entry(frame, width=50)
        birdeye_entry.grid(row=2, column=1, pady=5)
        
        def open_goplus():
            webbrowser.open("https://goplussecurity.io/signup")
            
        def open_birdeye():
            webbrowser.open("https://birdeye.so/api")
        
        def save_apis():
            goplus = goplus_entry.get().strip()
            birdeye = birdeye_entry.get().strip()
            
            if not (goplus or birdeye):
                messagebox.showerror("Error", "Please enter at least one API key")
                return
                
            self.config["apis"]["goplus"] = goplus
            self.config["apis"]["birdeye"] = birdeye
            self.api_var.set("✅")
            self.update_config_display()
            api_window.destroy()
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="GoPlus Signup", command=open_goplus).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Birdeye Signup", command=open_birdeye).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Save", command=save_apis).grid(row=0, column=2, padx=5)
    
    def update_config_display(self):
        """Update the configuration display"""
        self.config_text.delete(1.0, tk.END)
        
        # Format config for display
        display_config = {
            "Wallet": {
                "Address": self.config["wallet"]["address"][:8] + "..." if self.config["wallet"]["address"] else "Not Set",
                "Network": self.config["wallet"]["network"]
            },
            "RPC Endpoints": {
                "QuickNode": "Set ✅" if self.config["rpc"]["quicknode"] else "Not Set ❌",
                "Helius": "Set ✅" if self.config["rpc"]["helius"] else "Not Set ❌"
            },
            "API Keys": {
                "GoPlus": "Set ✅" if self.config["apis"]["goplus"] else "Not Set ❌",
                "Birdeye": "Set ✅" if self.config["apis"]["birdeye"] else "Not Set ❌"
            }
        }
        
        self.config_text.insert(1.0, json.dumps(display_config, indent=2))
    
    def verify_setup(self):
        """Verify all components are properly set up"""
        checks = []
        
        # Check wallet
        if self.config["wallet"]["address"]:
            checks.append("✅ Wallet configured")
        else:
            checks.append("❌ Wallet not configured")
        
        # Check RPC
        if self.config["rpc"]["quicknode"] or self.config["rpc"]["helius"]:
            checks.append("✅ At least one RPC endpoint configured")
        else:
            checks.append("❌ No RPC endpoints configured")
        
        # Check APIs
        if self.config["apis"]["goplus"] or self.config["apis"]["birdeye"]:
            checks.append("✅ At least one API key configured")
        else:
            checks.append("❌ No API keys configured")
        
        messagebox.showinfo("Setup Verification", "\n".join(checks))
    
    def save_and_exit(self):
        """Save configuration and exit"""
        if not self.config["wallet"]["address"]:
            if not messagebox.askyesno("Warning", "Wallet not configured. Save anyway?"):
                return
        
        self.save_config()
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.root.quit()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run()
