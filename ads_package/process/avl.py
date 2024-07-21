class AVLNode:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1


class AVLTree:
    def __init__(self, filename):
        self.root = None
        self.filename = filename

    def _height(self, node):
        if node is None:
            return 0
        return node.height

    def _update_height(self, node):
        if node is not None:
            node.height = max(self._height(node.left), self._height(node.right)) + 1

    def _balance_factor(self, node):
        if node is None:
            return 0
        return self._height(node.left) - self._height(node.right)

    def _rotate_left(self, y):
        x = y.right
        t2 = x.left

        x.left = y
        y.right = t2

        self._update_height(y)
        self._update_height(x)

        return x

    def _rotate_right(self, x):
        y = x.left
        t2 = y.right

        y.right = x
        x.left = t2

        self._update_height(x)
        self._update_height(y)

        return y

    def _balance(self, node):
        if node is None:
            return 0

        node.height = max(self._height(node.left), self._height(node.right)) + 1
        balance = self._balance_factor(node)

        if balance > 1:
            if self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1:
            if self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    def insert(self, key):
        self.root = self._insert(self.root, key)
        self._save_to_file()

    def _insert(self, node, key):
        if node is None:
            return AVLNode(key)

        if key < node.key:
            node.left = self._insert(node.left, key)
        else:
            node.right = self._insert(node.right, key)

        return self._balance(node)

    def _find_min(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def delete(self, key):
        self.root = self._delete(self.root, key)
        self._save_to_file()

    def _delete(self, node, key):
        if node is None:
            return node

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left
            temp = self._find_min(node.right)
            node.key = temp.key
            node.right = self._delete(node.right, temp.key)

        return self._balance(node)

    def _inorder(self, node, result):
        if node:
            self._inorder(node.left, result)
            result.append(node.key)
            self._inorder(node.right, result)

    def inorder(self):
        result = []
        self._inorder(self.root, result)
        return result

    def _save_to_file(self):
        with open(self.filename, "w") as f:
            self._write_tree(self.root, f)

    def _write_tree(self, node, f):
        if node:
            f.write(node.key + "\n")
            self._write_tree(node.left, f)
            self._write_tree(node.right, f)

    def load_from_file(self):
        try:
            with open(self.filename, "r") as f:
                lines = f.read().splitlines()
                self.root = None
                for line in lines:
                    self.root = self._insert(self.root, line)
        except FileNotFoundError:
            self.root = None


def main():
    filename = "Autocomplete.txt"
    avl_tree = AVLTree(filename)
    avl_tree.load_from_file()

    while True:
        print("\nAVL Tree Menu:")
        print("1. Insert a string")
        print("2. Delete a string")
        print("3. Display the AVL tree")
        print("4. Quit")

        choice = input("Enter your choice: ")

        if choice == "1":
            value = input("Enter a string to insert: ")
            avl_tree.insert(value)
            print(f"Inserted '{value}' into the AVL tree.")

        elif choice == "2":
            value = input("Enter a string to delete: ")
            avl_tree.delete(value)
            print(f"Deleted '{value}' from the AVL tree.")

        elif choice == "3":
            print("Inorder traversal of the AVL tree:", avl_tree.inorder())

        elif choice == "4":
            avl_tree._save_to_file()
            print("Exiting the program.")
            break

        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
