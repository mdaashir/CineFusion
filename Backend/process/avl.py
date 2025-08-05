"""
AVL Tree Implementation for CineFusion Backend
A self-balancing binary search tree for efficient movie title storage and retrieval
"""

from typing import Optional, List


class AVLNode:
    """Node class for AVL Tree"""

    def __init__(self, key: str) -> None:
        self.key = key
        self.left: Optional['AVLNode'] = None
        self.right: Optional['AVLNode'] = None
        self.height = 1


class AVLTree:
    """AVL Tree implementation with auto-balancing capabilities"""

    def __init__(self) -> None:
        self.root: Optional[AVLNode] = None

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
        """Insert a key into the AVL tree"""
        if not key or not isinstance(key, str):
            return False

        key = key.strip()
        if not key:
            return False

        self.root = self._insert(self.root, key)
        return True

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

    def search(self, key: str) -> bool:
        """Search for a key in the tree"""
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
        """Get inorder traversal of the tree (sorted order)"""
        result: List[str] = []
        self._inorder(self.root, result)
        return result

    def get_suggestions(self, prefix: str, max_suggestions: int = 10) -> List[str]:
        """Get autocomplete suggestions for a given prefix"""
        if not prefix:
            return []

        suggestions = []
        all_keys = self.inorder()

        prefix_lower = prefix.lower()
        for key in all_keys:
            if key.lower().startswith(prefix_lower):
                suggestions.append(key)
                if len(suggestions) >= max_suggestions:
                    break

        return suggestions

    def get_tree_stats(self) -> dict:
        """Get statistics about the tree"""
        def count_nodes(node: Optional[AVLNode]) -> int:
            if node is None:
                return 0
            return 1 + count_nodes(node.left) + count_nodes(node.right)

        return {
            'total_nodes': count_nodes(self.root),
            'height': self._height(self.root),
            'is_empty': self.root is None
        }


# Test the implementation if run directly
if __name__ == "__main__":
    # Simple test
    avl = AVLTree()
    test_movies = ["Avatar", "Avengers", "Batman", "Superman", "Spider-Man"]

    print("Testing AVL Tree implementation:")
    for movie in test_movies:
        avl.insert(movie)
        print(f"Inserted: {movie}")

    print(f"\nAll movies in sorted order: {avl.inorder()}")
    print(f"Suggestions for 'A': {avl.get_suggestions('A', 5)}")
    print(f"Search for 'Batman': {avl.search('Batman')}")
    print(f"Search for 'Joker': {avl.search('Joker')}")
    print(f"Tree stats: {avl.get_tree_stats()}")
