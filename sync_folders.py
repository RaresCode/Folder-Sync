import os
import shutil
import datetime
import argparse
import time

class FileSync:
    def __init__(self, src_path, rep_path, sync_time, log_path):
        """
        Initialize the FileSync object.
        """
        self.src_path = src_path
        self.rep_path = rep_path
        self.sync_time = sync_time
        self.log_path = log_path

    def set_log_file(self):
        """
        Checks if the log file exists; if not, it creates an empty log file.
        """
        if not os.path.exists(self.log_path):
            open(self.log_path, "w").close()

    def log_action(self, action, src_path, rep_path):
        """
        Logs a file operation (copy, delete, synchronization) along with the timestamp to the log file and console output.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, "a") as f:
            if src_path != "" and rep_path != "":
                f.write(f"[{timestamp}] - {action}: {src_path} > {rep_path}\n")
                print(f"[{timestamp}] - {action}: {src_path} > {rep_path}")
            else:
                f.write(f"[{timestamp}] - {action}\n")
                print(f"[{timestamp}] - {action}")

    def sync_scheduler(self):
        """
        Initiates the synchronization process. Periodically synchronizes the source folder with the replica folder at the specified sync_time interval.
        """
        self.set_log_file()
        while True:
            self.sync_files()
            self.log_action("Successfully synced", "", "")
            time.sleep(self.sync_time)

    def sync_files(self):
        """
        Synchronizes files from the source folder to the replica folder.
        """
        # Keep track of the created folders
        
        self.src_folders = []
        self.rep_folders = []
        self.src_files = []
        self.rep_files = []
        

        # Get the dirpaths and filenames for the source folder, append relative path for comparison
        for dirpath, _, filenames in os.walk(self.src_path):
            self.src_folders.append(os.path.relpath(dirpath))
            
            if filenames != None and filenames != []:
                for file_name in filenames:
                    
                    file_path = f"{dirpath}\{file_name}"
                    self.src_files.append(os.path.relpath(file_path))
        
        # Get the dirpaths and filenames for the replica folder, append relative path for comparison
        for dirpath, _, filenames in os.walk(self.rep_path):
            self.rep_folders.append(os.path.relpath(dirpath).replace("replica", "source"))
            
            if filenames != None and filenames != []:
                for file_name in filenames:
                    
                    file_path = f"{dirpath}\{file_name}"
                    self.rep_files.append(os.path.relpath(file_path).replace("replica", "source"))
        
        
        # Check if any items has been deleted from src:
        self._check_item_deletion()
        
        # Check if any items has been created
        self._check_item_creation()
        
        # Check if any items has been modified
        self._check_item_modification()
            

    def _check_item_creation(self):
        
        """
        Itterate over both folder directories and create directory in replica if not present
        We itterate over the dir first as file creation cannot be made when no dir exists
        """
        for folder in self.src_folders:
            if folder not in self.rep_folders:
                os.makedirs(folder.replace("source", "replica"))
                self.log_action("Created", folder, folder.replace("source", "replica"))
            
        
        """
        Itterate over both files and create files in replica if not present
        """
        for file_path in self.src_files:
            if file_path not in self.rep_files:
                shutil.copy2(file_path, file_path.replace('source', 'replica'))
                self.log_action("Created", file_path, file_path.replace('source', 'replica'))
            
                
    def _check_item_deletion(self):
        """
        Itterate over both folder directories and delete directory in replica if not present in src
        """
        for folder in self.rep_folders:
            if folder not in self.src_folders:
                # This except triggers when a subfolder has already been deleted
                try:
                    shutil.rmtree(folder.replace("source", "replica"))
                except FileNotFoundError:
                    self.log_action("Deleted", folder, folder.replace("source", "replica"))
            
        
        """
        Itterate over both files and delete files in replica if not present in src
        """
        for file_path in self.rep_files:
            if file_path not in self.src_files:
                # This except triggers when the file has already been deleted by the folder deletion
                try:
                    os.remove(file_path.replace("source", "replica"))
                except FileNotFoundError:
                    self.log_action("Deleted", file_path, file_path.replace("source", "replica"))

    def _get_file_time(self, path):
        """
        Gets the modification time of a file.
        """
        numeric_modification_time = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(numeric_modification_time)

    def _check_item_modification(self):
        """
        If the latest modify date in src does not match 
        the exact date in replica the item has been modified
        """
        for src_file, rep_file in zip(self.src_files, self.rep_files):
            if self._get_file_time(src_file) != self._get_file_time(rep_file.replace("source", "replica")):
                shutil.copy2(src_file, rep_file.replace("source", "replica"))
                self.log_action("Modified", src_file, rep_file.replace("source", "replica"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize src and rep")
    parser.add_argument("source_folder", help="Path to the source folder.")
    parser.add_argument("replica_folder", help="Path to the replica folder")
    parser.add_argument("sync_interval", type=int, help="Sync interval in seconds")
    parser.add_argument("log_file", help="Path to the log file.")
    # EXAMPLE USAGE: python sync_folders.py "D:\veeam task\source" "D:\veeam task\replica" 60 "D:\veeam task\log_file.txt"
    args = parser.parse_args()

    sync = FileSync(args.source_folder, args.replica_folder, args.sync_interval, args.log_file)
    sync.sync_scheduler()
