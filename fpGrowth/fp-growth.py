import pandas as pd
import itertools

class Node(object):

    # frequent pattern tree node

    def __init__(self, value, count, parent):

        # initialize the node

        self.value = value
        self.count = count
        self.parent = parent
        self.link = None
        self.children = []

    def get_child_node(self, value):

        # return the child node that contains the specific value

        for node in self.children:
            if node.value == value:
                return node

        return None

    def add_child_node(self, value):

        # add a child node with a specific value and return it

        child = Node(value, 1, self)
        self.children.append(child)
        return child


class FrequentPatternTree(object):

    # FPtree object

    def __init__(self, transactions, support_threshold, root_value, root_count):

        # initialize and build the FPtree

        self.frequent_items = self.get_frequent_items(transactions, support_threshold)
        self.headers = self.initialize_header_table(self.frequent_items)
        self.root = self.build_frequent_pattern_tree(
            transactions, root_value,
            root_count, self.frequent_items, self.headers)

    @staticmethod
    def get_frequent_items(transactions, support_threshold):

        # returns a dictionary of items who's support are above the support_threshold

        items = {}

        # For each item in each transaction,
        for transaction in transactions:
            for item in transaction:
                if item in items:
                    # if the item is already in the dictionary increase it's key value by 1
                    items[item] += 1
                else:
                    # if the item is not in the dictionary add it and set its key value to 1
                    items[item] = 1

        for key in list(items.keys()):
            # delete items who's support is below the support_threshold
            if items[key] < support_threshold:
                del items[key]

        return items

    @staticmethod
    def initialize_header_table(frequent_items):

        # initialize the header table for linking keys to their nodes.

        headers = {}
        for key in frequent_items.keys():
            headers[key] = None

        return headers

    def build_frequent_pattern_tree(self, transactions, root_value, root_count, frequent_items, headers):

        # build the frequent pattern tree and return its root node

        root_node = Node(root_value, root_count, None)

        for transaction in transactions:
            # sift through transactions to extract frequent items
            sorted_items = [x for x in transaction if x in frequent_items]
            # sort the list of frequent items by most frequent first
            sorted_items.sort(key=lambda x: frequent_items[x], reverse=True)
            # if the transaction contained frequent items, add them to the tree
            if len(sorted_items) > 0:
                self.insert_into_tree(sorted_items, root_node, headers)

        return root_node

    def insert_into_tree(self, items, node, headers):

        # grow the frequent pattern tree recursively.

        first_item = items[0]
        # check to see if the item is a child of it's parent
        child = node.get_child_node(first_item)
        # if so, increase its count by 1
        if child is not None:
            child.count += 1
        else:
            # otherwise, add a new child to the parent node.
            child = node.add_child_node(first_item)

            # if the item doesnt have a node reference in the header table, add it.
            if headers[first_item] is None:
                headers[first_item] = child
            # otherwise, if the node has a reference in the header table already,
            # link the new child to the last known occurrence of its header key
            else:
                current = headers[first_item]
                while current.link is not None:
                    current = current.link
                current.link = child

        # recurse until there are no remaining items in the list
        remaining_items = items[1:]
        if len(remaining_items) > 0:
            self.insert_into_tree(remaining_items, child, headers)

    def tree_has_single_path(self, node):

        # Check to see if the tree is a single path, if so return true, else false.

        number_of_children = len(node.children)
        # if more than one child, ret false
        if number_of_children > 1:
            return False
        # if there is no children, return true
        elif number_of_children == 0:
            return True
        # if there is one child, recursively check to see if it has a single path
        else:
            return True and self.tree_has_single_path(node.children[0])

    def search_for_patterns(self, support_threshold):

        # search through the FPtree for frequent patterns.

        # if the tree has a single path, generate a list of frequent patterns.
        if self.tree_has_single_path(self.root):
            return self.create_pattern_list()
        else:
            # if the tree is conditional (root value != null) search subtrees for patterns
            # and generate new frequent patterns by appending the key_value of it's root
            return self.append_root(self.search_sub_trees(support_threshold))

    def append_root(self, patterns):

        # Append value_of_root to patterns in the dictionary if we are in a conditional FPtree.

        value_of_root = self.root.value

        # if the value of the root is not null, we are in a conditional tree
        if value_of_root is not None:
            # create new patterns by appending the value of the root to patterns in the dictionary
            new_patterns = {}
            for key in patterns.keys():
                new_patterns[tuple(sorted(list(key) + [value_of_root]))] = patterns[key]

            return new_patterns

        return patterns

    def create_pattern_list(self):

        # create a list of patterns with their support counts.

        patterns = {}
        # get all frequent items from the tree
        items = self.frequent_items.keys()

        # if we are in a conditional tree, add the root value as a pattern.
        if self.root.value is None:
            value_of_root = []
        else:
            value_of_root = [self.root.value]
            patterns[tuple(value_of_root)] = self.root.count

        # find patterns by looking at combinations of frequent items
        # of size 1 -> length of frequent_items_list + 1
        for i in range(1, len(items) + 1):
            for combination in itertools.combinations(items, i):
                pattern = tuple(sorted(list(combination) + value_of_root))
                # let the support count of the new pattern be the support of the least frequent item
                patterns[pattern] = min([self.frequent_items[x] for x in combination])

        return patterns

    def search_sub_trees(self, support_threshold):

        # create subtrees and search them for frequent patterns.

        patterns = {}
        # generate a search_order list by sorting the items
        # by least number of occurrences first
        search_order = sorted(self.frequent_items.keys(),
                              key=lambda x: self.frequent_items[x])

        # insert items into tree
        for item in search_order:
            occurrences = []
            all_occurrence_paths_to_root = []
            # get item's node from the header table
            node = self.headers[item]

            # trace node links to get a list of all occurrences of an item.
            while node is not None:
                occurrences.append(node)
                node = node.link

            # for each occurrence of the item, trace it's path back to the root
            for occurrence in occurrences:
                frequency = occurrence.count
                path_to_root = []
                parent = occurrence.parent

                while parent.parent is not None:
                    path_to_root.append(parent.value)
                    parent = parent.parent
                for i in range(frequency):
                    all_occurrence_paths_to_root.append(path_to_root)

            # with the list of all occurrence paths to root, create a subtree and search it for patterns
            subtree = FrequentPatternTree(all_occurrence_paths_to_root, support_threshold,
                                          item, self.frequent_items[item])
            subtree_patterns = subtree.search_for_patterns(support_threshold)

            # add subtree patterns the patterns dictionary.
            for pattern in subtree_patterns.keys():
                # if pattern already exits, increase it's count by it's frequency
                if pattern in patterns:
                    patterns[pattern] += subtree_patterns[pattern]
                # otherwise add the pattern with it's frequency
                else:
                    patterns[pattern] = subtree_patterns[pattern]

        return patterns


def mine_frequent_patterns(transactions, support_threshold):

    # Given a list of transactions and a support threshold,
    # build an FPtree and search it for frequent patterns
    FPtree = FrequentPatternTree(transactions, support_threshold, None, None)
    # Search the FPtree to get a list of frequent patterns
    return FPtree.search_for_patterns(support_threshold)


def get_association_rules(patterns, confidence_threshold):

    # Given a set of frequent itemsets, print out strong association rules

    rules = {}
    for itemset in patterns.keys():
        # Get the support of AUB
        union_support = patterns[itemset]

        for i in range(1, len(itemset)):
            # find each combination of the antecedent
            for antecedent in itertools.combinations(itemset, i):

                # get the antecedent
                antecedent = tuple(sorted(antecedent))

                # get the consequent
                consequent = tuple(sorted(set(itemset) - set(antecedent)))
                if len(set(consequent)) == 0:
                    consequent = antecedent

                # if the antecedent is a known pattern
                if antecedent in patterns:
                    # Get support of A
                    antecedent_support = patterns[antecedent]

                    # Calculate the confidence via support AUB/support A
                    confidence = float(union_support) / antecedent_support

                    # if the support AUB/support of A is >= the confidence threshold, add the rule
                    if antecedent != consequent:
                        if confidence >= confidence_threshold:
                            print(antecedent,'->', consequent,',', confidence)
    return rules


def main():

    # Read data from csv file into a dataframe
    data = pd.read_csv("transactions.csv")

    # Group items (index) by Member_number and Date
    grouped_df = data.groupby(['Member_number', 'Date'])

    # Create a list of transactions
    transactions = []
    for group, group_column in grouped_df:
        transactions.append(group_column['itemDescription'].values.tolist())

    # Threshold vars
    support_threshold = 20
    confidence_threshold = .02

    # Generate frequent patterns for the transactions with support_threshold of n
    patterns = mine_frequent_patterns(transactions, support_threshold)

    # Output Rules
    print('Support Threshold: ', support_threshold)
    print('Confidence Threshold: ', confidence_threshold*100, '%')
    print('------------------------------------------')
    print('(Antecedent) -> (Consequent), Confidence')
    print('------------------------------------------')

    get_association_rules(patterns, confidence_threshold)


if __name__ == "__main__":
    main()
