<?php
/**
 * HTML to WordPress Page Importer
 * 
 * This script imports HTML pages into WordPress, including text content and images
 */

// Ensure this is being run in WordPress context
require_once('wp-load.php');

class HTMLToWordPressImporter {
    private $html_directory;
    private $image_directory;
    
    public function __construct($html_dir, $image_dir = null) {
        $this->html_directory = rtrim($html_dir, '/');
        $this->image_directory = $image_dir ? rtrim($image_dir, '/') : $html_dir . '/images';
    }
    
    public function import() {
        $html_files = glob($this->html_directory . '/*.html');
        
        foreach ($html_files as $html_file) {
            $this->process_html_file($html_file);
        }
    }
    
    private function process_html_file($file_path) {
        // Load HTML content
        $html_content = file_get_contents($file_path);
        if (!$html_content) {
            error_log("Failed to read file: " . $file_path);
            return;
        }
        
        // Create DOM document
        $doc = new DOMDocument();
        @$doc->loadHTML(mb_convert_encoding($html_content, 'HTML-ENTITIES', 'UTF-8'));
        
        // Get page title
        $title = basename($file_path, '.html');
        $title_nodes = $doc->getElementsByTagName('title');
        if ($title_nodes->length > 0) {
            $title = $title_nodes->item(0)->nodeValue;
        }
        
        // Get main content (assuming it's in a main content div/article)
        $content = '';
        $main_content = $doc->getElementsByTagName('main');
        if ($main_content->length === 0) {
            $main_content = $doc->getElementsByTagName('article');
        }
        if ($main_content->length === 0) {
            $main_content = $doc->getElementsByTagName('body');
        }
        
        if ($main_content->length > 0) {
            $content = $doc->saveHTML($main_content->item(0));
        } else {
            $content = $doc->saveHTML();
        }
        
        // Process images
        $content = $this->process_images($content);
        
        // Create WordPress page
        $page_data = array(
            'post_title'    => wp_strip_all_tags($title),
            'post_content'  => $content,
            'post_status'   => 'publish',
            'post_type'     => 'page'
        );
        
        // Check if page already exists
        $existing_page = get_page_by_title($title, OBJECT, 'page');
        
        if ($existing_page) {
            $page_data['ID'] = $existing_page->ID;
            wp_update_post($page_data);
            echo "Updated page: " . $title . "\n";
        } else {
            wp_insert_post($page_data);
            echo "Created new page: " . $title . "\n";
        }
    }
    
    private function process_images($content) {
        // Create upload directory if it doesn't exist
        $upload_dir = wp_upload_dir();
        
        if (!file_exists($upload_dir['path'])) {
            wp_mkdir_p($upload_dir['path']);
        }
        
        // Find all images in content
        $doc = new DOMDocument();
        @$doc->loadHTML(mb_convert_encoding($content, 'HTML-ENTITIES', 'UTF-8'));
        $images = $doc->getElementsByTagName('img');
        
        foreach ($images as $image) {
            $src = $image->getAttribute('src');
            
            // Skip if already a full URL
            if (filter_var($src, FILTER_VALIDATE_URL)) {
                continue;
            }
            
            // Get image path
            $img_path = $this->image_directory . '/' . basename($src);
            
            if (file_exists($img_path)) {
                // Prepare image for WordPress
                $file_array = array(
                    'name'     => basename($img_path),
                    'tmp_name' => $img_path
                );
                
                // Check file type
                $wp_filetype = wp_check_filetype(basename($img_path), null);
                
                // Prepare attachment data
                $attachment = array(
                    'post_mime_type' => $wp_filetype['type'],
                    'post_title'     => preg_replace('/\.[^.]+$/', '', basename($img_path)),
                    'post_content'   => '',
                    'post_status'    => 'inherit'
                );
                
                // Insert attachment into WordPress
                $attach_id = wp_insert_attachment($attachment, $img_path);
                
                if ($attach_id) {
                    // Include image.php if not already loaded
                    require_once(ABSPATH . 'wp-admin/includes/image.php');
                    
                    // Generate attachment metadata and update
                    $attach_data = wp_generate_attachment_metadata($attach_id, $img_path);
                    wp_update_attachment_metadata($attach_id, $attach_data);
                    
                    // Update image src in content
                    $new_src = wp_get_attachment_url($attach_id);
                    $content = str_replace($src, $new_src, $content);
                }
            }
        }
        
        return $content;
    }
}

// Usage example (uncomment and modify paths as needed):
/*
$importer = new HTMLToWordPressImporter(
    '/path/to/html/files',  // Directory containing HTML files
    '/path/to/images'       // Directory containing images (optional)
);
$importer->import();
*/
