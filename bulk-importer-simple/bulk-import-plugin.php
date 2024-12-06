<?php
/*
Plugin Name: Simple HTML Importer
Description: Basic HTML page importer
Version: 1.0
*/

// Add admin menu
add_action('admin_menu', 'bulk_importer_menu');

function bulk_importer_menu() {
    add_menu_page(
        'HTML Importer',
        'HTML Importer',
        'manage_options',
        'html-importer',
        'importer_page'
    );
}

// Register plugin settings
add_action('admin_init', 'bulk_importer_settings');

function bulk_importer_settings() {
    register_setting('html_importer_group', 'html_importer_header_id');
    register_setting('html_importer_group', 'html_importer_footer_id');
    
    // Add settings section
    add_settings_section(
        'html_importer_section',
        'Template Settings',
        'html_importer_section_callback',
        'html_importer_group'
    );
    
    // Add settings fields
    add_settings_field(
        'html_importer_header_id',
        'Header Template ID',
        'html_importer_header_callback',
        'html_importer_group',
        'html_importer_section'
    );
    
    add_settings_field(
        'html_importer_footer_id',
        'Footer Template ID',
        'html_importer_footer_callback',
        'html_importer_group',
        'html_importer_section'
    );
}

function html_importer_section_callback() {
    echo '<p>Enter your Elementor template IDs below. You can find these by going to Templates in Elementor.</p>';
}

function html_importer_header_callback() {
    $header_id = get_option('html_importer_header_id');
    echo '<input type="text" name="html_importer_header_id" value="' . esc_attr($header_id) . '" class="regular-text">';
    if ($header_id) {
        echo '<p class="description">Current header template ID: ' . esc_html($header_id) . '</p>';
    }
}

function html_importer_footer_callback() {
    $footer_id = get_option('html_importer_footer_id');
    echo '<input type="text" name="html_importer_footer_id" value="' . esc_attr($footer_id) . '" class="regular-text">';
    if ($footer_id) {
        echo '<p class="description">Current footer template ID: ' . esc_html($footer_id) . '</p>';
    }
}

function importer_page() {
    if (!current_user_can('manage_options')) {
        wp_die('You do not have sufficient permissions to access this page.');
    }
    
    // Check if settings were updated
    if (isset($_GET['settings-updated'])) {
        add_settings_error(
            'html_importer_messages',
            'html_importer_message',
            'Settings Saved',
            'updated'
        );
    }
    
    ?>
    <div class="wrap">
        <h1>HTML Importer</h1>
        
        <?php
        // Show error/update messages
        settings_errors('html_importer_messages');
        ?>
        
        <!-- Settings Section -->
        <div class="card">
            <h2>Template Settings</h2>
            <form method="post" action="options.php">
                <?php
                settings_fields('html_importer_group');
                do_settings_sections('html_importer_group');
                submit_button('Save Settings');
                
                // Display current values
                $header_id = get_option('html_importer_header_id');
                $footer_id = get_option('html_importer_footer_id');
                if ($header_id || $footer_id) {
                    echo '<hr>';
                    echo '<h3>Current Settings</h3>';
                    echo '<ul>';
                    if ($header_id) {
                        echo '<li><strong>Header Template ID:</strong> ' . esc_html($header_id) . '</li>';
                    }
                    if ($footer_id) {
                        echo '<li><strong>Footer Template ID:</strong> ' . esc_html($footer_id) . '</li>';
                    }
                    echo '</ul>';
                }
                ?>
            </form>
        </div>

        <!-- Import Section -->
        <h2>Import Pages</h2>
        <form method="post" action="">
            <?php wp_nonce_field('html_import_action', 'html_import_nonce'); ?>
            <table class="form-table">
                <tr>
                    <th scope="row">Website URL</th>
                    <td>
                        <input type="url" name="website_url" class="regular-text" 
                               value="https://historicaviationmilitary.com" required>
                    </td>
                </tr>
            </table>
            <p class="submit">
                <input type="submit" name="scan_website" class="button button-primary" value="Scan Website">
            </p>
        </form>

        <?php
        // Handle website scanning
        if (isset($_POST['scan_website']) && check_admin_referer('html_import_action', 'html_import_nonce')) {
            $url = esc_url_raw($_POST['website_url']);
            
            try {
                $response = wp_remote_get($url);
                if (is_wp_error($response)) {
                    throw new Exception('Failed to connect to website');
                }

                $html = wp_remote_retrieve_body($response);
                $dom = new DOMDocument();
                @$dom->loadHTML($html, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD);
                $xpath = new DOMXPath($dom);

                // Find all links
                $links = $xpath->query('//a[@href]');
                $found_pages = array();

                foreach ($links as $link) {
                    $href = $link->getAttribute('href');
                    if (strpos($href, '.html') !== false) {
                        $found_pages[] = array(
                            'url' => $href,
                            'title' => $link->textContent
                        );
                    }
                }

                if (!empty($found_pages)) {
                    echo '<h3>Found Pages</h3>';
                    echo '<form method="post">';
                    wp_nonce_field('import_pages_action', 'import_pages_nonce');
                    echo '<table class="widefat">';
                    echo '<thead><tr><th>Select</th><th>URL</th><th>Title</th><th>Status</th></tr></thead>';
                    foreach ($found_pages as $page) {
                        $status = get_page_status($page['url']);
                        $row_class = $status['imported'] ? 'imported-page' : '';
                        
                        echo '<tr class="' . $row_class . '">';
                        echo '<td><input type="checkbox" name="pages[]" value="' . esc_attr($page['url']) . '"></td>';
                        echo '<td>' . esc_html($page['url']) . '</td>';
                        echo '<td>' . esc_html($page['title']) . '</td>';
                        
                        // Status column
                        echo '<td>';
                        if ($status['imported']) {
                            echo 'Imported: ' . date('Y-m-d H:i:s', $status['import_time']) . '<br>';
                            echo 'Status: ' . ucfirst($status['page_status']) . '<br>';
                            echo '<a href="' . get_edit_post_link($status['page_id']) . '" target="_blank">Edit Page</a> | ';
                            echo '<a href="' . get_permalink($status['page_id']) . '" target="_blank">View Page</a>';
                        } else {
                            echo 'Not imported';
                        }
                        echo '</td>';
                        echo '</tr>';
                    }
                    echo '</table>';
                    echo '<p class="submit">';
                    echo '<input type="submit" name="import_pages" class="button button-primary" value="Import Selected Pages">';
                    echo '</p>';
                    echo '</form>';
                } else {
                    echo '<div class="notice notice-warning"><p>No HTML pages found.</p></div>';
                }
            } catch (Exception $e) {
                echo '<div class="notice notice-error"><p>Error: ' . esc_html($e->getMessage()) . '</p></div>';
            }
        }
        ?>
        
        <!-- Cleanup Section -->
        <h2>Cleanup Imported Pages</h2>
        <form method="post">
            <?php wp_nonce_field('cleanup_pages_action', 'cleanup_pages_nonce'); ?>
            <p>
                <input type="submit" name="cleanup_pages" class="button button-secondary" value="Cleanup Imported Pages">
            </p>
        </form>
        
        <?php
        // Handle cleanup form submission
        if (isset($_POST['cleanup_pages']) && check_admin_referer('cleanup_pages_action', 'cleanup_pages_nonce')) {
            $deleted = cleanup_imported_pages();
            if ($deleted > 0) {
                echo '<div class="notice notice-success"><p>' . 
                     sprintf('%d imported page(s) cleaned up. Backup created at %s', 
                            $deleted, 
                            date('Y-m-d H:i:s', get_option('html_importer_last_cleanup_time'))) . 
                     '</p></div>';
            } else {
                echo '<div class="notice notice-info"><p>No imported pages found to clean up.</p></div>';
            }
        }
        ?>
        
        <style>
            .imported-page { background-color: #f0f7ff; }
            .widefat td { vertical-align: top; }
        </style>
    </div>
    <?php
}

function cleanup_imported_pages() {
    // Get all pages that were imported by our plugin
    $args = array(
        'post_type' => 'page',
        'posts_per_page' => -1,
        'meta_query' => array(
            array(
                'key' => '_imported_source_url',
                'compare' => 'EXISTS'
            )
        )
    );
    
    $query = new WP_Query($args);
    $deleted = 0;
    $backup = array();
    
    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            $id = get_the_ID();
            
            // Create backup of page data
            $backup[] = array(
                'id' => $id,
                'title' => get_the_title(),
                'content' => get_the_content(),
                'source_url' => get_post_meta($id, '_imported_source_url', true),
                'import_time' => get_post_meta($id, '_import_timestamp', true),
                'meta' => get_post_meta($id)
            );
            
            wp_delete_post($id, true);
            $deleted++;
        }
        
        // Save backup if pages were deleted
        if ($deleted > 0) {
            $backup_time = current_time('Y-m-d_H-i-s');
            update_option('html_importer_last_backup_' . $backup_time, $backup);
            update_option('html_importer_last_cleanup_time', time());
        }
    }
    
    wp_reset_postdata();
    return $deleted;
}

function get_page_status($url) {
    $args = array(
        'post_type' => 'page',
        'meta_query' => array(
            array(
                'key' => '_imported_source_url',
                'value' => $url
            )
        )
    );
    
    $query = new WP_Query($args);
    $status = array(
        'imported' => false,
        'import_time' => null,
        'page_id' => null,
        'page_status' => null,
        'is_manual' => false
    );
    
    if ($query->have_posts()) {
        while ($query->have_posts()) {
            $query->the_post();
            $id = get_the_ID();
            $status['imported'] = true;
            $status['import_time'] = get_post_meta($id, '_import_timestamp', true);
            $status['page_id'] = $id;
            $status['page_status'] = get_post_status();
        }
    }
    
    wp_reset_postdata();
    return $status;
}

function import_html_page($url, $title) {
    try {
        $response = wp_remote_get($url);
        if (is_wp_error($response)) {
            throw new Exception('Failed to fetch page content');
        }

        $html = wp_remote_retrieve_body($response);
        $dom = new DOMDocument();
        @$dom->loadHTML($html, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD);
        $xpath = new DOMXPath($dom);

        // Extract content (simplified for example)
        $content = '';
        $nodes = $xpath->query('//body');
        if ($nodes->length > 0) {
            $content = $dom->saveHTML($nodes->item(0));
        }

        // Create page
        $post_data = array(
            'post_title'    => $title,
            'post_content'  => $content,
            'post_status'   => 'draft',
            'post_type'     => 'page'
        );

        $page_id = wp_insert_post($post_data);
        if (is_wp_error($page_id)) {
            throw new Exception('Failed to create page');
        }

        // Add meta data
        update_post_meta($page_id, '_imported_source_url', $url);
        update_post_meta($page_id, '_import_timestamp', time());
        update_post_meta($page_id, '_elementor_edit_mode', 'builder');

        // Add header template if set
        $header_id = get_option('html_importer_header_id');
        if ($header_id) {
            update_post_meta($page_id, '_header_template_id', $header_id);
        }

        // Add footer template if set
        $footer_id = get_option('html_importer_footer_id');
        if ($footer_id) {
            update_post_meta($page_id, '_footer_template_id', $footer_id);
        }

        return true;
    } catch (Exception $e) {
        return new WP_Error('import_failed', $e->getMessage());
    }
}

// Handle the import form submission
if (isset($_POST['import_pages']) && check_admin_referer('import_pages_action', 'import_pages_nonce')) {
    if (empty($_POST['pages'])) {
        echo '<div class="notice notice-error"><p>Please select pages to import.</p></div>';
    } else {
        $imported = 0;
        $errors = array();

        foreach ($_POST['pages'] as $url) {
            $title = basename($url, '.html');
            $result = import_html_page($url, $title);
            
            if (is_wp_error($result)) {
                $errors[] = $result->get_error_message();
            } else {
                $imported++;
            }
        }

        if ($imported > 0) {
            echo '<div class="notice notice-success"><p>' . 
                 sprintf('%d page(s) imported successfully at %s', $imported, date('Y-m-d H:i:s')) . 
                 '</p></div>';
        }
        if (!empty($errors)) {
            echo '<div class="notice notice-error"><p>Errors:<br>' . 
                 implode('<br>', array_map('esc_html', $errors)) . 
                 '</p></div>';
        }
    }
}
