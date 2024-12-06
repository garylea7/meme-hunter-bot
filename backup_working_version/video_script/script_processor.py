import pandas as pd
import docx
import yaml
from pathlib import Path
from typing import Dict, List, Optional

class ScriptProcessor:
    def __init__(self, script_path: str):
        self.script_path = Path(script_path)
        self.segments = []
        
    def load_script(self) -> None:
        """Load the script from various supported formats"""
        if self.script_path.suffix == '.docx':
            self._load_docx()
        elif self.script_path.suffix == '.txt':
            self._load_txt()
        else:
            raise ValueError(f"Unsupported file format: {self.script_path.suffix}")
            
    def _load_docx(self) -> None:
        """Load script from a Word document"""
        doc = docx.Document(self.script_path)
        for para in doc.paragraphs:
            if para.text.strip():
                self.segments.append({
                    'text': para.text,
                    'timestamp': None,
                    'duration': None
                })
                
    def _load_txt(self) -> None:
        """Load script from a text file"""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self.segments.append({
                        'text': line.strip(),
                        'timestamp': None,
                        'duration': None
                    })
    
    def export_to_csv(self, output_path: str) -> None:
        """Export the script segments to CSV"""
        df = pd.DataFrame(self.segments)
        df.to_csv(output_path, index=False)
        
    def export_to_yaml(self, output_path: str) -> None:
        """Export the script segments to YAML"""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.segments, f, allow_unicode=True)

def main():
    # Example usage
    processor = ScriptProcessor("example_script.docx")
    processor.load_script()
    processor.export_to_csv("output.csv")
    processor.export_to_yaml("output.yaml")

if __name__ == "__main__":
    main()
