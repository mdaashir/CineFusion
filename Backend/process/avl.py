"""
AVL Tree Implementation for CineFusion
A self-balancing binary search tree for efficient movie title storage and retrieval
"""

import os
import logging
from typing import Optional, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AVLNode:
    """
    Node class for AVL Tree
    """
    def __init__(self, key: str) -> None:
        self.key = key
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height = 1


class AVLTree:
    """
    AVL Tree implementation with auto-balancing capabilities
    """

    def __init__(self, filename: str = "Autocomplete.txt") -> None:
        self.root: Optional[AVLNode] = None
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the data file exists"""
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    f.write("")
                logger.info(f"Created new file: {self.filename}")
            except IOError as e:
                logger.error(f"Failed to create file {self.filename}: {e}")
                raise

    def _height(self, node: Optional[AVLNode]) -> int:
        """Get height of a node"""
        if node is None:
            return 0
        return node.height

    def _update_height(self, node: Optional[AVLNode]) -> None:
        """Update height of a node"""
        if node is not None:
            node.height = max(self._height(node.left), self._height(node.right)) + 1

    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        """Calculate balance factor of a node"""
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _rotate_left(self, y: AVLNode) -> AVLNode:
        """Perform left rotation"""
        x = y.right
        if x is None:
            return y

        t2 = x.left
        x.left = y
        y.right = t2

        self._update_height(y)
        self._update_height(x)
        return x

    def _rotate_right(self, x: AVLNode) -> AVLNode:
        """Perform right rotation"""
        y = x.left
        if y is None:
            return x

        t2 = y.right
        y.right = x
        x.left = t2

        self._update_height(x)
        self._update_height(y)
        return y

    def _balance(self, node: Optional[AVLNode]) -> Optional[AVLNode]:
        """Balance the tree at given node"""
        if node is None:
            return None

        node.height = max(self._height(node.left), self._height(node.right)) + 1
        balance = self._balance_factor(node)

        # Left heavy
        if balance > 1:
            if node.left and self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Right heavy
        if balance < -1:
            if node.right and self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def insert(self, key: str) -> bool:
        """
        Insert a key into the AVL tree

        Args:
            key (str): The key to insert

        Returns:
            bool: True if insertion was successful
        """
        try:
            if not key or not isinstance(key, str):
                logger.warning(f"Invalid key provided: {key}")
                return False

            key = key.strip()
            if not key:
                return False

            old_root = self.root
            self.root = self._insert(self.root, key)

            # Only save if tree structure changed
            if self.root != old_root:
                self._save_to_file()
                logger.info(f"Inserted key: {key}")

            return True
        except Exception as e:
            logger.error(f"Error inserting key {key}: {e}")
            return False

    def _insert(self, node: Optional[AVLNode], key: str) -> AVLNode:
        """Internal insert method"""
        if node is None:
            return AVLNode(key)

        # Avoid duplicates
        if key == node.key:
            return node
        elif key < node.key:
            node.left = self._insert(node.left, key)
        else:
            node.right = self._insert(node.right, key)

        return self._balance(node)

    def _find_min(self, node: AVLNode) -> AVLNode:
        """Find minimum value node in subtree"""
        current = node
        while current.left is not None:
            current = current.left
        return current

    def delete(self, key: str) -> bool:
        """
        Delete a key from the AVL tree

        Args:
            key (str): The key to delete

        Returns:
            bool: True if deletion was successful
        """
        try:
            if not key or not isinstance(key, str):
                return False

            key = key.strip()
            if not key:
                return False

            old_root = self.root
            self.root = self._delete(self.root, key)

            # Only save if tree structure changed
            if self.root != old_root:
                self._save_to_file()
                logger.info(f"Deleted key: {key}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False

    def _delete(self, node: Optional[AVLNode], key: str) -> Optional[AVLNode]:
        """Internal delete method"""
        if node is None:
            return node

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node to be deleted found
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            # Node has two children
            temp = self._find_min(node.right)
            node.key = temp.key
            node.right = self._delete(node.right, temp.key)

        return self._balance(node)

    def search(self, key: str) -> bool:
        """
        Search for a key in the tree

        Args:
            key (str): The key to search for

        Returns:
            bool: True if key exists in tree
        """
        if not key:
            return False
        return self._search(self.root, key.strip())

    def _search(self, node: Optional[AVLNode], key: str) -> bool:
        """Internal search method"""
        if node is None:
            return False

        if key == node.key:
            return True
        elif key < node.key:
            return self._search(node.left, key)
        else:
            return self._search(node.right, key)

    def _inorder(self, node: Optional[AVLNode], result: List[str]) -> None:
        """Internal inorder traversal method"""
        if node:
            self._inorder(node.left, result)
            result.append(node.key)
            self._inorder(node.right, result)

    def inorder(self) -> List[str]:
        """
        Get inorder traversal of the tree

        Returns:
            List[str]: List of keys in sorted order
        """
        result: List[str] = []
        self._inorder(self.root, result)
        return result

    def get_suggestions(self, prefix: str, max_suggestions: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for a given prefix

        Args:
            prefix (str): The prefix to search for
            max_suggestions (int): Maximum number of suggestions to return

        Returns:
            List[str]: List of suggestions starting with the prefix
        """
        if not prefix:
            return []

        suggestions = []
        all_keys = self.inorder()

        for key in all_keys:
            if key.lower().startswith(prefix.lower()):
                suggestions.append(key)
                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

    def _save_to_file(self) -> bool:
        """Save tree contents to file"""
        try:
            with open(self.filename, "w", encoding='utf-8') as f:
                self._write_tree(self.root, f)
            return True
        except IOError as e:
            logger.error(f"Error saving to file {self.filename}: {e}")
            return False

    def _write_tree(self, node: Optional[AVLNode], f) -> None:
        """Internal method to write tree nodes to file"""
        if node:
            f.write(node.key + "\n")
            self._write_tree(node.left, f)
            self._write_tree(node.right, f)

    def load_from_file(self) -> bool:
        """
        Load tree contents from file

        Returns:
            bool: True if loading was successful
        """
        try:
            if not os.path.exists(self.filename):
                logger.warning(f"File {self.filename} does not exist")
                return False

            with open(self.filename, "r", encoding='utf-8') as f:
                lines = f.read().splitlines()
                self.root = None

                for line in lines:
                    line = line.strip()
                    if line:  # Skip empty lines
                        self.root = self._insert(self.root, line)

            logger.info(f"Loaded {len(lines)} entries from {self.filename}")
            return True
        except IOError as e:
            logger.error(f"Error loading from file {self.filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading file: {e}")
            return False

    def get_tree_stats(self) -> dict:
        """
        Get statistics about the tree

        Returns:
            dict: Dictionary containing tree statistics
        """
        def count_nodes(node: Optional[AVLNode]) -> int:
            if node is None:
                return 0
            return 1 + count_nodes(node.left) + count_nodes(node.right)

        return {
            'total_nodes': count_nodes(self.root),
            'height': self._height(self.root),
            'is_empty': self.root is None
        }


def main():
    """Main function for interactive AVL tree operations"""
    try:
        filename = "Autocomplete.txt"
        avl_tree = AVLTree(filename)

        # Load existing data
        if avl_tree.load_from_file():
            print(f"Loaded existing data from {filename}")
        else:
            print(f"Starting with empty tree")

        while True:
            print("\n" + "="*50)
            print("CineFusion AVL Tree Manager")
            print("="*50)
            print("1. Insert a movie title")
            print("2. Delete a movie title")
            print("3. Search for a title")
            print("4. Display all titles (sorted)")
            print("5. Get autocomplete suggestions")
            print("6. Show tree statistics")
            print("7. Quit")
            print("-"*50)

            try:
                choice = input("Enter your choice (1-7): ").strip()

                if choice == "1":
                    title = input("Enter movie title to insert: ").strip()
                    if title:
                        if avl_tree.insert(title):
                            print(f"✓ Successfully inserted '{title}'")
                        else:
                            print(f"✗ Failed to insert '{title}' (may already exist)")
                    else:
                        print("✗ Empty title not allowed")

                elif choice == "2":
                    title = input("Enter movie title to delete: ").strip()
                    if title:
                        if avl_tree.delete(title):
                            print(f"✓ Successfully deleted '{title}'")
                        else:
                            print(f"✗ Title '{title}' not found")
                    else:
                        print("✗ Empty title not allowed")

                elif choice == "3":
                    title = input("Enter movie title to search: ").strip()
                    if title:
                        if avl_tree.search(title):
                            print(f"✓ Found '{title}' in the tree")
                        else:
                            print(f"✗ '{title}' not found in the tree")
                    else:
                        print("✗ Empty title not allowed")

                elif choice == "4":
                    titles = avl_tree.inorder()
                    if titles:
                        print(f"\nAll movie titles ({len(titles)} total):")
                        print("-" * 40)
                        for i, title in enumerate(titles, 1):
                            print(f"{i:3d}. {title}")
                    else:
                        print("No titles in the tree")

                elif choice == "5":
                    prefix = input("Enter prefix for suggestions: ").strip()
                    if prefix:
                        suggestions = avl_tree.get_suggestions(prefix, 10)
                        if suggestions:
                            print(f"\nSuggestions for '{prefix}':")
                            print("-" * 30)
                            for i, suggestion in enumerate(suggestions, 1):
                                print(f"{i:2d}. {suggestion}")
                        else:
                            print(f"No suggestions found for '{prefix}'")
                    else:
                        print("✗ Empty prefix not allowed")

                elif choice == "6":
                    stats = avl_tree.get_tree_stats()
                    print(f"\nTree Statistics:")
                    print("-" * 20)
                    print(f"Total nodes: {stats['total_nodes']}")
                    print(f"Tree height: {stats['height']}")
                    print(f"Is empty: {stats['is_empty']}")

                elif choice == "7":
                    print("Saving data and exiting...")
                    avl_tree._save_to_file()
                    print("✓ Data saved successfully")
                    print("Thank you for using CineFusion AVL Tree Manager!")
                    break

                else:
                    print("✗ Invalid choice. Please select 1-7.")

            except KeyboardInterrupt:
                print("\n\nProgram interrupted. Saving data...")
                avl_tree._save_to_file()
                print("✓ Data saved. Goodbye!")
                break
            except Exception as e:
                print(f"✗ An error occurred: {e}")
                logger.error(f"Unexpected error in main loop: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize AVL Tree: {e}")
        print(f"✗ Failed to initialize: {e}")


if __name__ == "__main__":
    main()
