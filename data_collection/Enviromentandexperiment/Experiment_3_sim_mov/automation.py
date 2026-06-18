#!/usr/bin/env python3
"""
MASTER AUTOMATION SCRIPT - CORRECTED PATHS
Runs all Gazebo world files from your Rooms_exp/Exp5 structure
Collects LIDAR data and creates master CSV with metadata
"""

import os
import sys
import subprocess
import time
import csv
import json
import glob
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

# ============================================================================
# CONFIGURATION - UPDATED FOR Exp6.1mov MOVEMENT EXPERIMENT
# ============================================================================

# Worlds for movement experiment
WORLDS_DIR = Path("/home/hernan/gazebo_worlds/Rooms_exp/Exp6.1mov/generated_worlds_mov1")

# Plugin path (unchanged)
PLUGIN_PATH = Path("/home/hernan/gazebo_worlds/lidar_plugin/build")

# Scripts directory (unchanged)
SCRIPTS_DIR = Path("/home/hernan/gazebo_worlds")
VER_LIDAR_SCRIPT = SCRIPTS_DIR / "ver_lidar.py"
LIDAR_TO_CSV_SCRIPT = SCRIPTS_DIR / "lidar_to_csv.py"

# Temporary files
LIDAR_SCAN_FILE = Path("/tmp/lidar_scan.txt")
LIDAR_CSV_OUTPUT = SCRIPTS_DIR / "lidar_scan.csv"

# Results directory for this experiment
RESULTS_DIR = Path("/home/hernan/gazebo_worlds/Rooms_exp/Exp6.1mov/experiment_results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Master CSV output
MASTER_CSV = RESULTS_DIR / "master_experiments_mov1.csv"

# Timing
GAZEBO_STARTUP = 5
DATA_COLLECTION_TIME = 3
GAZEBO_SHUTDOWN = 2


print(f"""
╔════════════════════════════════════════════════════════════════════════╗
║                    CONFIGURATION CHECK                                 ║
╚════════════════════════════════════════════════════════════════════════╝

Worlds directory: {WORLDS_DIR}
Plugin path: {PLUGIN_PATH}
Scripts directory: {SCRIPTS_DIR}
Results directory: {RESULTS_DIR}
Master CSV: {MASTER_CSV}

Checking if directories exist...
""")

if WORLDS_DIR.exists():
    print(f"✅ Worlds directory exists: {WORLDS_DIR}")
    world_files = list(WORLDS_DIR.glob("*.world"))
    print(f"   Found {len(world_files)} .world files")
else:
    print(f"❌ Worlds directory NOT found: {WORLDS_DIR}")
    print(f"   Please check the path is correct")

if PLUGIN_PATH.exists():
    print(f"✅ Plugin path exists: {PLUGIN_PATH}")
else:
    print(f"❌ Plugin path NOT found: {PLUGIN_PATH}")

if VER_LIDAR_SCRIPT.exists():
    print(f"✅ ver_lidar.py exists: {VER_LIDAR_SCRIPT}")
else:
    print(f"❌ ver_lidar.py NOT found: {VER_LIDAR_SCRIPT}")

if LIDAR_TO_CSV_SCRIPT.exists():
    print(f"✅ lidar_to_csv.py exists: {LIDAR_TO_CSV_SCRIPT}")
else:
    print(f"❌ lidar_to_csv.py NOT found: {LIDAR_TO_CSV_SCRIPT}")

print()

# ============================================================================
# WORLD FILE PARSER
# ============================================================================

class WorldFileParser:
    """Parse world filename to extract metadata"""
    
    @staticmethod
    def parse_filename(world_filename):
        """
        Extract metadata from world filename
        Works with various naming conventions
        """
        try:
            # Remove .world extension
            name = world_filename.replace('.world', '')
            
            metadata = {
                'world_file': world_filename,
                'environment_id': name,  # Use full name as ID
            }
            
            # Try to extract resolution (e.g., res4.0deg, 4.0deg, 4deg)
            res_patterns = [
                r'res([\d.]+)deg',
                r'([\d.]+)deg',
                r'res_?([\d.]+)',
            ]
            
            for pattern in res_patterns:
                res_match = re.search(pattern, name)
                if res_match:
                    try:
                        res_val = float(res_match.group(1))
                        metadata['resolution'] = res_val
                        metadata['resolution_label'] = f"{res_val}°"
                        break
                    except:
                        pass
            
            # Try to extract samples (e.g., 90samp, 90samples)
            samp_patterns = [
                r'(\d+)samp',
                r'(\d+)samples',
            ]
            
            for pattern in samp_patterns:
                samp_match = re.search(pattern, name)
                if samp_match:
                    try:
                        metadata['samples'] = int(samp_match.group(1))
                        break
                    except:
                        pass
            
            # Try to extract obstacles (e.g., o13, obs13)
            obs_patterns = [
                r'_o(\d+)',
                r'obs_?(\d+)',
            ]
            
            for pattern in obs_patterns:
                obs_match = re.search(pattern, name)
                if obs_match:
                    try:
                        metadata['num_obstacles'] = int(obs_match.group(1))
                        break
                    except:
                        pass
            
            # Try to extract room size (e.g., r8.8x5.9, 8.8x5.9)
            size_patterns = [
                r'_r([\d.]+)x([\d.]+)',
                r'([\d.]+)x([\d.]+)m',
            ]
            
            for pattern in size_patterns:
                size_match = re.search(pattern, name)
                if size_match:
                    try:
                        width = float(size_match.group(1))
                        height = float(size_match.group(2))
                        area = width * height
                        
                        if area < 30:
                            category = "small"
                        elif area < 60:
                            category = "medium"
                        else:
                            category = "large"
                        
                        metadata['room_width'] = width
                        metadata['room_height'] = height
                        metadata['room_size'] = f"{width}x{height}m"
                        metadata['area_category'] = category
                        break
                    except:
                        pass
            
            return metadata
        
        except Exception as e:
            print(f"[WARN] Could not parse {world_filename}: {e}")
            return {'world_file': world_filename, 'environment_id': name}

# ============================================================================
# GAZEBO CONTROLLER
# ============================================================================

class GazeboController:
    """Control Gazebo server startup/shutdown"""
    
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.gzserver = None
    
    def start(self, world_file):
        """Start Gazebo server with world file"""
        self.stop()  # Ensure previous instance is killed
        time.sleep(1)
        
        env = os.environ.copy()
        env['GAZEBO_PLUGIN_PATH'] = str(self.plugin_path)
        
        print(f"  [GAZEBO] Starting server with {world_file.name}...")
        
        try:
            self.gzserver = subprocess.Popen(
                ["gzserver", "--verbose", str(world_file)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for startup
            time.sleep(GAZEBO_STARTUP)
            
            if self.gzserver.poll() is not None:
                print(f"  [ERROR] Gazebo failed to start")
                return False
            
            print(f"  [OK] Gazebo running")
            return True
        
        except Exception as e:
            print(f"  [ERROR] Failed to start Gazebo: {e}")
            return False
    
    def stop(self):
        """Stop Gazebo server"""
        if self.gzserver:
            try:
                self.gzserver.terminate()
                self.gzserver.wait(timeout=GAZEBO_SHUTDOWN)
            except:
                self.gzserver.kill()
        
        # Ensure all processes killed
        os.system("pkill -9 gzserver 2>/dev/null")
        os.system("pkill -9 gzclient 2>/dev/null")
        time.sleep(1)

# ============================================================================
# DATA COLLECTOR
# ============================================================================

class DataCollector:
    """Collect LIDAR data from running Gazebo"""
    
    def __init__(self, ver_lidar_script, csv_script, lidar_csv_output):
        self.ver_lidar_script = ver_lidar_script
        self.csv_script = csv_script
        self.lidar_csv_output = lidar_csv_output
    
    def collect(self, world_metadata):
        """
        Collect LIDAR data from current Gazebo instance
        Returns: list of dicts with LIDAR measurements
        """
        print(f"  [DATA] Collecting LIDAR data...")
        
        try:
            # Run visualization (non-blocking, just for stability)
            vis_proc = subprocess.Popen(
                ["python3", str(self.ver_lidar_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for data to stabilize
            time.sleep(DATA_COLLECTION_TIME)
            
            # Kill visualization
            vis_proc.terminate()
            try:
                vis_proc.wait(timeout=1)
            except:
                vis_proc.kill()
            
            # Run CSV conversion
            print(f"  [DATA] Converting to CSV...")
            csv_proc = subprocess.run(
                ["python3", str(self.csv_script)],
                capture_output=True,
                timeout=10,
                text=True
            )
            
            # Read generated CSV
            if not self.lidar_csv_output.exists():
                print(f"  [WARN] CSV not created at {self.lidar_csv_output}")
                return None
            
            # Parse CSV and add metadata
            data = []
            try:
                with open(self.lidar_csv_output, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Add world metadata to each row
                        row.update(world_metadata)
                        data.append(row)
            
            except Exception as e:
                print(f"  [ERROR] Failed to read CSV: {e}")
                return None
            
            print(f"  [OK] Collected {len(data)} measurements")
            return data
        
        except Exception as e:
            print(f"  [ERROR] Data collection failed: {e}")
            return None

# ============================================================================
# MASTER AUTOMATION
# ============================================================================

class MasterAutomation:
    """Run all experiments and aggregate data"""
    
    def __init__(self):
        self.gazebo = GazeboController(PLUGIN_PATH)
        self.collector = DataCollector(
            VER_LIDAR_SCRIPT, LIDAR_TO_CSV_SCRIPT, LIDAR_CSV_OUTPUT
        )
        self.parser = WorldFileParser()
        
        self.all_data = []
        self.experiments_run = 0
        self.start_time = datetime.now()
    
    def find_world_files(self):
        """Find all .world files"""
        world_files = sorted(glob.glob(str(WORLDS_DIR / "*.world")))
        
        if not world_files:
            print(f"[ERROR] No world files found in {WORLDS_DIR}")
            return []
        
        print(f"[OK] Found {len(world_files)} world files")
        return [Path(f) for f in world_files]
    
    def run_all_experiments(self):
        """Run all world files and collect data"""
        
        print(f"\n{'='*70}")
        print(f"MASTER AUTOMATION - RUNNING ALL EXPERIMENTS")
        print(f"{'='*70}")
        
        # Find world files
        world_files = self.find_world_files()
        if not world_files:
            return False
        
        total = len(world_files)
        
        try:
            for exp_num, world_file in enumerate(world_files, 1):
                print(f"\n[EXP {exp_num}/{total}] {world_file.name}")
                
                # Parse world filename
                metadata = self.parser.parse_filename(world_file.name)
                print(f"  Metadata: {metadata}")
                
                # Start Gazebo
                if not self.gazebo.start(world_file):
                    print(f"  [SKIP] Failed to start Gazebo")
                    continue
                
                # Collect data
                data = self.collector.collect(metadata)
                
                # Stop Gazebo
                self.gazebo.stop()
                
                # Save data
                if data:
                    self.all_data.extend(data)
                    self.experiments_run += 1
                    
                    # Progress
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    rate = self.experiments_run / elapsed if elapsed > 0 else 0
                    remaining = (total - exp_num) / rate if rate > 0 else 0
                    
                    print(f"  Progress: {self.experiments_run}/{total} | "
                          f"Elapsed: {elapsed/60:.1f}min | "
                          f"Est. remaining: {remaining/60:.1f}min")
        
        except KeyboardInterrupt:
            print(f"\n[INTERRUPT] User stopped")
        
        finally:
            self.gazebo.stop()
        
        return True
    
    def save_master_csv(self):
        """Save all data to master CSV"""
        
        if not self.all_data:
            print(f"[ERROR] No data collected")
            return False
        
        print(f"\n{'='*70}")
        print(f"SAVING MASTER CSV")
        print(f"{'='*70}")
        
        # Convert to DataFrame
        df = pd.DataFrame(self.all_data)
        
        # Reorder columns for readability
        column_order = [
            'timestamp', 'quality', 'angle_deg', 'distance_mm',
            'world_file', 'environment_id'
        ]
        
        # Add optional columns if they exist
        optional_cols = ['resolution', 'resolution_label', 'samples', 
                        'num_obstacles', 'room_width', 'room_height', 
                        'room_size', 'area_category']
        
        for col in optional_cols:
            if col in df.columns:
                column_order.append(col)
        
        # Keep only columns that exist
        available_cols = [c for c in column_order if c in df.columns]
        df = df[available_cols]
        
        # Save
        df.to_csv(MASTER_CSV, index=False)
        
        print(f"[OK] Saved: {MASTER_CSV}")
        print(f"[OK] Total rows: {len(df)}")
        print(f"[OK] Unique environments: {df['environment_id'].nunique()}")
        
        # Show sample
        print(f"\n[SAMPLE] First 3 rows:")
        print(df.head(3).to_string())
        
        return True
    
    def generate_report(self):
        """Generate summary report"""
        
        if not self.all_data:
            return
        
        df = pd.read_csv(MASTER_CSV)
        
        report_file = RESULTS_DIR / "experiment_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("MASTER AUTOMATION - EXPERIMENT SUMMARY\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Total measurements: {len(df)}\n")
            f.write(f"Unique environments: {df['environment_id'].nunique()}\n")
            f.write(f"Experiments completed: {self.experiments_run}\n\n")
            
            # Statistics by resolution
            if 'resolution' in df.columns:
                f.write("MEASUREMENTS BY RESOLUTION:\n")
                f.write("-"*70 + "\n")
                res_stats = df.groupby('resolution').agg({
                    'distance_mm': ['count', 'mean', 'std']
                }).round(2)
                f.write(res_stats.to_string())
                f.write("\n\n")
            
            # Statistics by area
            if 'area_category' in df.columns:
                f.write("MEASUREMENTS BY ROOM SIZE:\n")
                f.write("-"*70 + "\n")
                area_stats = df.groupby('area_category').agg({
                    'distance_mm': ['count', 'mean', 'std']
                }).round(2)
                f.write(area_stats.to_string())
                f.write("\n\n")
            
            f.write("="*70 + "\n")
            f.write("OUTPUT FILES:\n")
            f.write("="*70 + "\n")
            f.write(f"Master CSV: {MASTER_CSV}\n")
            f.write(f"Summary: {report_file}\n")
            f.write("\nYou can now:\n")
            f.write("1. Open master CSV in Excel/Calc\n")
            f.write("2. Filter by environment, resolution, room size\n")
            f.write("3. Run DBSCAN clustering on each group\n")
        
        print(f"\n[OK] Report saved: {report_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"\n{'='*70}")
    print(f"MASTER AUTOMATION - RUN ALL GAZEBO WORLDS")
    print(f"{'='*70}\n")
    
    # Check if scripts exist
    if not VER_LIDAR_SCRIPT.exists():
        print(f"[ERROR] ver_lidar.py not found at {VER_LIDAR_SCRIPT}")
        print(f"Please check the path is correct")
        return False
    
    if not LIDAR_TO_CSV_SCRIPT.exists():
        print(f"[ERROR] lidar_to_csv.py not found at {LIDAR_TO_CSV_SCRIPT}")
        print(f"Please check the path is correct")
        return False
    
    if not WORLDS_DIR.exists():
        print(f"[ERROR] Worlds directory not found at {WORLDS_DIR}")
        print(f"Please check the path is correct")
        return False
    
    # Run automation
    automation = MasterAutomation()
    
    success = automation.run_all_experiments()
    
    if success and automation.all_data:
        automation.save_master_csv()
        automation.generate_report()
        
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS! All experiments completed")
        print(f"{'='*70}")
        print(f"\nMaster CSV is ready at: {MASTER_CSV}")
        print(f"\nResults directory: {RESULTS_DIR}")
        print(f"\nYou can now:")
        print(f"  1. Open in Excel/Calc")
        print(f"  2. Filter and analyze data")
        print(f"  3. Run DBSCAN clustering")
        
        return True
    
    else:
        print(f"\n[ERROR] No data collected or experiments failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] User stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)