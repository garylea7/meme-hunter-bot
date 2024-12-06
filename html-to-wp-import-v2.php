<?php
/**
 * Enhanced HTML to WordPress Page Importer
 * Handles multiple page layouts and content structures
 */

require_once('wp-load.php');

class EnhancedHTMLToWordPressImporter {
    private $html_directory;
    private $image_directory;
    private $debug_mode;
    
    public function __construct($html_dir, $image_dir = null, $debug = false) {
        $this->html_directory = rtrim($html_dir, '/');
        $this->image_directory = $image_dir ? rtrim($image_dir, '/') : $html_dir;
        $this->debug_mode = $debug;
    }
    
    public function analyze_page($url, $output_file = null) {
        // Fetch HTML content
        $html_content = file_get_contents($url);
        if (!$html_content) {
            return "Failed to fetch URL: " . $url;
        }
        
        // Create DOM document
        $doc = new DOMDocument();
        @$doc->loadHTML(mb_convert_encoding($html_content, 'HTML-ENTITIES', 'UTF-8'), LIBXML_NOERROR);
        
        $analysis = [];
        $analysis['url'] = $url;
        
        // Get page title
        $titles = $doc->getElementsByTagName('title');
        $analysis['title'] = $titles->length > 0 ? $titles->item(0)->nodeValue : '';
        
        // Analyze tables
        $tables = $doc->getElementsByTagName('table');
        $analysis['tables'] = [];
        
        foreach ($tables as $index => $table) {
            $tableInfo = $this->analyze_table($table);
            $analysis['tables'][] = $tableInfo;
        }
        
        // Find main content
        $analysis['main_content'] = $this->identify_main_content($doc);
        
        // Analyze images
        $images = $doc->getElementsByTagName('img');
        $analysis['images'] = [];
        
        foreach ($images as $img) {
            $analysis['images'][] = [
                'src' => $img->getAttribute('src'),
                'alt' => $img->getAttribute('alt'),
                'location' => $this->determine_image_location($img)
            ];
        }
        
        // Output analysis
        $output = $this->format_analysis($analysis);
        
        if ($output_file) {
            file_put_contents($output_file, $output);
            return "Analysis saved to " . $output_file;
        }
        
        return $output;
    }
    
    private function analyze_table($table) {
        $rows = $table->getElementsByTagName('tr');
        $info = [
            'rows' => $rows->length,
            'cells' => [],
            'has_menu' => false,
            'has_images' => false,
            'content_type' => 'unknown'
        ];
        
        // Check if this might be the 12-cell menu table
        if ($rows->length == 2 && $rows->item(1)->getElementsByTagName('td')->length == 12) {
            $info['content_type'] = 'menu';
            $info['has_menu'] = true;
        }
        
        // Analyze cells
        foreach ($rows as $row) {
            $cells = $row->getElementsByTagName('td');
            $cellInfo = [];
            
            foreach ($cells as $cell) {
                $images = $cell->getElementsByTagName('img');
                $links = $cell->getElementsByTagName('a');
                
                $cellContent = [
                    'has_image' => $images->length > 0,
                    'has_links' => $links->length > 0,
                    'text_content' => trim(strip_tags($cell->nodeValue))
                ];
                
                if ($images->length > 0) {
                    $info['has_images'] = true;
                }
                
                $cellInfo[] = $cellContent;
            }
            
            $info['cells'][] = $cellInfo;
        }
        
        // Determine if this is likely a layout table
        if ($info['has_images'] && count($info['cells']) <= 3) {
            $info['content_type'] = 'layout';
        }
        
        return $info;
    }
    
    private function identify_main_content($doc) {
        // First try to find a table with the main content
        $tables = $doc->getElementsByTagName('table');
        foreach ($tables as $table) {
            $cells = $table->getElementsByTagName('td');
            foreach ($cells as $cell) {
                // If cell has substantial text content and images, it might be main content
                $text_length = strlen(trim(strip_tags($cell->nodeValue)));
                $images = $cell->getElementsByTagName('img');
                if ($text_length > 200 || $images->length > 0) {
                    return $this->clean_content($cell);
                }
            }
        }
        
        // Fallback to body content
        $body = $doc->getElementsByTagName('body')->item(0);
        return $this->clean_content($body);
    }
    
    private function clean_content($node) {
        $content = $node->ownerDocument->saveHTML($node);
        // Remove unnecessary tables and formatting
        $content = preg_replace('/<table[^>]*>.*?<\/table>/si', '', $content);
        return trim($content);
    }
    
    private function determine_image_location($img) {
        $parent = $img->parentNode;
        while ($parent && $parent->nodeName !== 'body') {
            if ($parent->nodeName === 'td') {
                // Check if this td is in the first/last row or first/last column
                $tr = $parent->parentNode;
                $table = $tr->parentNode;
                
                $rows = $table->getElementsByTagName('tr');
                $firstRow = $rows->item(0);
                $lastRow = $rows->item($rows->length - 1);
                
                if ($tr === $firstRow) return 'header';
                if ($tr === $lastRow) return 'footer';
                
                // Check if it's in a sidebar
                $cells = $tr->getElementsByTagName('td');
                $firstCell = $cells->item(0);
                $lastCell = $cells->item($cells->length - 1);
                
                if ($parent === $firstCell) return 'left-sidebar';
                if ($parent === $lastCell) return 'right-sidebar';
                
                return 'main-content';
            }
            $parent = $parent->parentNode;
        }
        return 'unknown';
    }
    
    private function format_analysis($analysis) {
        $output = "Page Analysis for: " . $analysis['url'] . "\n\n";
        $output .= "Title: " . $analysis['title'] . "\n\n";
        
        $output .= "Tables Found: " . count($analysis['tables']) . "\n";
        foreach ($analysis['tables'] as $index => $table) {
            $output .= "\nTable " . ($index + 1) . ":\n";
            $output .= "- Rows: " . $table['rows'] . "\n";
            $output .= "- Is Menu Table: " . ($table['has_menu'] ? 'Yes' : 'No') . "\n";
            $output .= "- Has Images: " . ($table['has_images'] ? 'Yes' : 'No') . "\n";
            $output .= "- Content Type: " . $table['content_type'] . "\n";
        }
        
        $output .= "\nImages Found: " . count($analysis['images']) . "\n";
        foreach ($analysis['images'] as $index => $img) {
            $output .= "\nImage " . ($index + 1) . ":\n";
            $output .= "- Source: " . $img['src'] . "\n";
            $output .= "- Location: " . $img['location'] . "\n";
            if ($img['alt']) $output .= "- Alt Text: " . $img['alt'] . "\n";
        }
        
        $output .= "\nMain Content Preview:\n";
        $output .= substr(strip_tags($analysis['main_content']), 0, 500) . "...\n";
        
        return $output;
    }
}

// Example usage:
/*
$importer = new EnhancedHTMLToWordPressImporter(
    '/path/to/html/files',
    '/path/to/images',
    true  // Enable debug mode
);

// Analyze a single page
$analysis = $importer->analyze_page(
    'https://historicaviationmilitary.com/burtonwoodhome897.html',
    'analysis_output.txt'
);
echo $analysis;
*/
