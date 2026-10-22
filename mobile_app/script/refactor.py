import os
import shutil
import re

# File map: source -> destination
# Using relative paths from mobile_app/lib
move_map = {
    # Auth
    "screens/cs_login_screen.dart": "features/auth/presentation/cs_login_screen.dart",
    
    # Home
    "screens/cs_home_screen.dart": "features/home/presentation/cs_home_screen.dart",
    
    # Rooms
    "screens/cs_rooms_screen.dart": "features/rooms/presentation/cs_rooms_screen.dart",
    "screens/cs_showtimes_screen.dart": "features/rooms/presentation/cs_showtimes_screen.dart",
    "screens/cs_seat_map_screen.dart": "features/rooms/presentation/cs_seat_map_screen.dart",
    "widgets/cs_movie_card.dart": "features/rooms/presentation/widgets/cs_movie_card.dart",
    "widgets/cs_seat_map.dart": "features/rooms/presentation/widgets/cs_seat_map.dart",
    
    # Alerts / Incidents
    "screens/cs_warning_screen.dart": "features/alerts/presentation/cs_warning_screen.dart",
    "screens/cs_warning_detail_screen.dart": "features/alerts/presentation/cs_warning_detail_screen.dart",
    "screens/cs_add_incident_screen.dart": "features/alerts/presentation/cs_add_incident_screen.dart",
    "screens/cs_damaged_seat_screen.dart": "features/alerts/presentation/cs_damaged_seat_screen.dart",
    "screens/cs_handover_screen.dart": "features/alerts/presentation/cs_handover_screen.dart",
    "screens/cs_incident_detail_screen.dart": "features/alerts/presentation/cs_incident_detail_screen.dart",
    
    # Scanner
    "screens/cs_scan_history_screen.dart": "features/scanner/presentation/cs_scan_history_screen.dart",
    "widgets/cs_scan_result_view.dart": "features/scanner/presentation/widgets/cs_scan_result_view.dart",
    
    # Settings
    "screens/cs_settings_screen.dart": "features/settings/presentation/cs_settings_screen.dart",
    
    # Notifications
    "screens/cs_notification_screen.dart": "features/notifications/presentation/cs_notification_screen.dart",
    
    # Core
    "screens/cs_offline_screen.dart": "core/network/presentation/cs_offline_screen.dart",
    "widgets/cs_app_card.dart": "core/widgets/cs_app_card.dart",
    "widgets/cs_bottom_nav.dart": "core/widgets/cs_bottom_nav.dart",
    "widgets/cs_primary_button.dart": "core/widgets/cs_primary_button.dart",
    "widgets/cs_screen_header.dart": "core/widgets/cs_screen_header.dart",
    "widgets/cs_status_tag.dart": "core/widgets/cs_status_tag.dart",
}

def main():
    lib_dir = "lib"
    
    # Step 1: Compute mapping for import replacements
    # e.g., 'package:mobile_app/screens/cs_login_screen.dart' -> 'package:mobile_app/features/auth/presentation/cs_login_screen.dart'
    # And relative imports: 'cs_login_screen.dart' -> 'features/auth/presentation/cs_login_screen.dart' (will be handled by forcing everything to package:)
    
    # We will convert ALL relative imports involving the moved files to package imports first,
    # then replace the package imports.
    
    all_dart_files = []
    for root, dirs, files in os.walk("."):
        if ".dart_tool" in root or ".idea" in root or "build" in root:
            continue
        for f in files:
            if f.endswith(".dart"):
                all_dart_files.append(os.path.join(root, f))
                
    # We also need to map the base names because many files use relative imports like:
    # import '../widgets/cs_app_card.dart';
    
    def get_package_path(rel_lib_path):
        return f"package:mobile_app/{rel_lib_path}"
        
    # Dictionary to replace any import path (basename or relative) with new package path
    # But wait, a simple regex is better. 
    # Find `import '.../basename.dart';` and replace with `import 'package:mobile_app/new_path/basename.dart';`
    
    basename_to_new_pkg = {}
    for old_rel, new_rel in move_map.items():
        basename = os.path.basename(old_rel)
        basename_to_new_pkg[basename] = get_package_path(new_rel)
        
    for dart_file in all_dart_files:
        with open(dart_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Replace imports line by line
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                # Check if it imports any of the moved files
                for basename, new_pkg in basename_to_new_pkg.items():
                    # match `import '.../basename.dart';` or `import 'basename.dart';`
                    if re.search(r"import\s+['\"].*?" + re.escape(basename) + r"['\"];", line):
                        lines[i] = f"import '{new_pkg}';"
                        
        new_content = '\n'.join(lines)
        
        if new_content != content:
            with open(dart_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
    # Step 2: Move files
    for old_rel, new_rel in move_map.items():
        old_path = os.path.join(lib_dir, old_rel)
        new_path = os.path.join(lib_dir, new_rel)
        
        if os.path.exists(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.move(old_path, new_path)
            print(f"Moved {old_path} -> {new_path}")
        else:
            print(f"NOT FOUND: {old_path}")

    # Remove the empty directories if possible
    try:
        os.rmdir(os.path.join(lib_dir, "screens"))
        os.rmdir(os.path.join(lib_dir, "widgets"))
    except:
        pass

if __name__ == "__main__":
    main()
