import os
import shutil
from bs4 import BeautifulSoup, Tag
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Define a handler class to manage resume file events
class ResumeHandler(FileSystemEventHandler):
    # Method called when a file is modified
    def on_modified(self, event):
        print(event)
        # Ignore directories
        if event.is_directory:
            return
        if "resume_old.html" in event.src_path:
            return
        # Propagate changes from the modified file
        self.propagate_changes(event.src_path)

    def propagate_changes(self, file_path):
        print(file_path)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            new_content = file.read()
            new_soup = BeautifulSoup(new_content, "html.parser")

        # Adjust this line to create a path string with the correct file name
        old_path = file_path.replace(".html", "_old.html")
        print(old_path)
        with open(old_path, "r", encoding="utf-8", errors="ignore") as file:
            old_content = file.read()
            old_soup = BeautifulSoup(old_content, "html.parser")

        new_elements, old_elements = self.identify_changes(old_soup, new_soup)

        for child_path in self.find_child_resumes(file_path):
            self.update_child_resume(child_path, new_elements, old_elements)

        self.update_old_resume(file_path)

    # Method to identify changes between original and new content
    def identify_changes(self, old_soup, new_soup):
        old_elements = []
        new_elements = []

        # Navigate to the <body> tag in both original and new content
        old_body = old_soup.body
        new_body = new_soup.body

        # Check if both bodies are not None before proceeding
        if old_body is not None and new_body is not None:
            # Recursively compare elements
            self.compare_elements(old_body, new_body, old_elements, new_elements)

        print(old_elements)
        print(new_elements)
        return new_elements, old_elements

    def compare_elements(self, old_elem, new_elem, old_elements, new_elements):
        # Base case: if elements are different, add the lowest level element and its parent to old_elements
        if old_elem != new_elem:
            # If the elements are Tag objects and have children, compare the children
            if hasattr(old_elem, "children") and hasattr(new_elem, "children"):
                for old_child, new_child in zip(old_elem.children, new_elem.children):
                    self.compare_elements(
                        old_child, new_child, old_elements, new_elements
                    )
            else:
                if new_elem.parent is not None:
                    new_elements.append(new_elem.parent)
                if old_elem.parent is not None:
                    old_elements.append(old_elem.parent)

    # Method to find child resumes related to a parent resume
    def find_child_resumes(self, parent_path):
        # Get the directory containing the parent resume
        parent_dir = os.path.dirname(parent_path)

        # Find all subdirectories in the parent directory
        child_dirs = [
            os.path.join(parent_dir, d)
            for d in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, d))
        ]

        # Initialize a list to store paths to child resumes
        child_paths = []

        # Iterate over each subdirectory
        for child_dir in child_dirs:
            # Recursively find resumes in subdirectories
            for root, dirs, files in os.walk(child_dir):
                for file in files:
                    # If a resume is found, add its path to the list
                    if file == "resume.html":
                        child_paths.append(os.path.join(root, file))

        return child_paths

    # Method to update child resumes with changed elements
    def update_child_resume(self, child_path, new_elements, old_elements):
        print(child_path)
        # Read child resume content and parse it
        with open(child_path, "r", encoding="utf-8", errors="ignore") as file:
            child_content = file.read()
            child_soup = BeautifulSoup(child_content, "html.parser")

        # Replace changed elements in child resume
        for new_elem, old_elem in zip(new_elements, old_elements):
            # Find all elements in the child resume that match the name and attributes of old_elem
            matching_elements = child_soup.find_all(
                name=old_elem.name, attrs=old_elem.attrs
            )
            # Iterate over all matching elements
            for elem in matching_elements:
                # If the text of elem matches the text of old_elem, replace it with new_elem
                if elem.text == old_elem.text:
                    elem.replace_with(new_elem)
                    # Once the element is replaced, break out of the loop to avoid replacing other elements with the same text
                    break

        # Write updated content back to child resume
        with open(child_path, "w", encoding="utf-8") as file:
            file.write(str(child_soup))

        # After updating the child resume, update its old resume
        self.update_old_resume(child_path)

    def update_old_resume(self, path):
        """
        This function updates the resume_old.html file with the content of resume.html.
        """
        with open(path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
        old_path = path.replace(".html", "_old.html")
        with open(old_path, "w", encoding="utf-8") as file:
            file.write(content)


# Main execution
if __name__ == "__main__":
    # Create an observer to watch for file events
    observer = Observer()
    handler = ResumeHandler()
    # Set the observer to use the handler and watch a specific directory
    observer.schedule(handler, path="root", recursive=True)
    observer.start()

    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        # Stop the observer when script is interrupted
        observer.stop()

    # Wait for the observer to finish
    observer.join()
