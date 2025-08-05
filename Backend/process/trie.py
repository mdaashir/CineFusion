"""
Backend-only Trie Implementation for CineFusion
A clean implementation without GUI components for API use
"""

class TrieNode:
    """Node class for Trie data structure"""
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False

class Trie:
    """
    Trie data structure for efficient autocomplete and prefix searching
    This is a backend-only implementation without any GUI components
    """

    def __init__(self):
        self.root = TrieNode()
        self.suggestions_list = []

    def insert(self, word: str):
        """Insert a word into the trie"""
        if not word:
            return

        node = self.root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def formTrie(self, keys: list):
        """Build trie from a list of keys/words"""
        for key in keys:
            if key and isinstance(key, str):
                self.insert(key.strip())

    def _suggestion_rec(self, node: TrieNode, word: str):
        """Recursive helper function to collect suggestions"""
        if len(self.suggestions_list) >= 20:  # Limit suggestions
            return

        if node.is_end_of_word:
            self.suggestions_list.append(word)

        for char, child_node in node.children.items():
            if len(self.suggestions_list) < 20:
                self._suggestion_rec(child_node, word + char)

    def printAutoSuggestions(self, prefix: str):
        """
        Get autocomplete suggestions for a given prefix
        Returns a list of suggestions or special codes:
        - 0: No suggestions found (prefix not in trie)
        - -1: Prefix exists but no completions available
        - list: Valid suggestions
        """
        if not prefix:
            return 0

        node = self.root
        self.suggestions_list = []

        # Navigate to the prefix node
        for char in prefix.lower():
            if char not in node.children:
                return 0  # Prefix not found
            node = node.children[char]

        # If no children, the prefix itself is a complete word but no suggestions
        if not node.children:
            return -1

        # Collect suggestions
        self._suggestion_rec(node, prefix.lower())

        return self.suggestions_list if self.suggestions_list else 0

    def search(self, word: str) -> bool:
        """Search if a word exists in the trie"""
        if not word:
            return False

        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]

        return node.is_end_of_word

    def get_all_words_with_prefix(self, prefix: str, max_results: int = 10) -> list:
        """Get all words that start with the given prefix"""
        if not prefix:
            return []

        node = self.root

        # Navigate to prefix
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]

        # Collect words
        results = []
        self._collect_words(node, prefix.lower(), results, max_results)
        return results

    def _collect_words(self, node: TrieNode, current_word: str, results: list, max_results: int):
        """Helper function to collect words starting from a node"""
        if len(results) >= max_results:
            return

        if node.is_end_of_word:
            results.append(current_word)

        for char, child_node in node.children.items():
            if len(results) < max_results:
                self._collect_words(child_node, current_word + char, results, max_results)

Node = TrieNode

# Only load data if this file is run directly (not imported)
if __name__ == "__main__":
    # Test the implementation
    trie = Trie()
    test_words = ["avatar", "avengers", "action", "adventure", "amazing", "spider", "spiderman"]
    trie.formTrie(test_words)

    print("Testing Trie implementation:")
    print(f"Suggestions for 'av': {trie.printAutoSuggestions('av')}")
    print(f"Suggestions for 'spi': {trie.printAutoSuggestions('spi')}")
    print(f"Search 'avatar': {trie.search('avatar')}")
    print(f"Search 'batman': {trie.search('batman')}")
