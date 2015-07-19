import unittest
import os

from base import ItemTreeRoot, ItemTree, Leaf

URL_PREFIX = "https://www.example.com/"

class BasicTreeConstructionTests(unittest.TestCase):

    def create_tree_root_test(self):
        """Check ItemTreeRoot can be correctly instantiated"""
        root = ItemTreeRoot(name="foo", url_prefix=URL_PREFIX)
        self.assertEqual(root.url_prefix, URL_PREFIX)
        self.assertEqual(root.name, "foo")

    def create_tree_test(self):
        """Check ItemTree can be correctly instantiated"""
        root = ItemTreeRoot(name="foo")
        tree = ItemTree(
            name="bar",
            parent=root,
            items = []
        )
        self.assertEqual(tree.name, "bar")
        self.assertEqual(tree.items, [])
        self.assertEqual(tree.parent, root)

    def create_leaf_test(self):
        """Check that Leaf can be correctly instantiated"""
        root = ItemTreeRoot(name="foo")
        leaf = Leaf(name="bar", parent=root)
        self.assertEqual(leaf.name, "bar")
        self.assertEqual(leaf.parent, root)

    def assure_url_prefix_test(self):
        """Check that the url prefix always has a "/"
           as the last character.
        """
        root = ItemTreeRoot(name="foo", url_prefix="https://foo_bar")
        self.assertEqual(root.url_prefix, "https://foo_bar/")
        root = ItemTreeRoot(name="foo", url_prefix="https://foo_bar/")
        self.assertEqual(root.url_prefix, "https://foo_bar/")
        root.url_prefix = "https://foo_baz"
        self.assertEqual(root.url_prefix, "https://foo_baz/")
        root.url_prefix = "https://foo_baz/"
        self.assertEqual(root.url_prefix, "https://foo_baz/")

class AdvancedTreeTests(unittest.TestCase):

    def setUp(self):
        root = ItemTreeRoot(name="root", url_prefix=URL_PREFIX)
        tree0 = ItemTree(name="level0", parent=root)
        root.items = [tree0]
        tree10 = ItemTree(name="level10", parent=tree0)
        tree11 = ItemTree(name="level11", parent=tree0)
        tree0.items = [tree10, tree11]
        item0 = Leaf(name="item0.tar.gz", parent=tree0)
        item100 = Leaf(name="item100.tar.gz", parent=tree10)
        item101 = Leaf(name="item101.tar.gz", parent=tree10)
        tree0.items.append(item0)
        tree10.items.append(item100)
        tree10.items.append(item101)
        self.root = root
        self.tree0 = tree0
        self.tree10 = tree10
        self.tree11 = tree11
        self.item0 = item0
        self.item100 = item100
        self.item101 = item101

    def full_tree_test(self):
        """Check that a full tree can be correctly constructed"""
        # check tree root
        self.assertIsNone(self.root.parent)
        self.assertIsNotNone(self.root.items)
        self.assertEquals(self.root.items, [self.tree0])
        self.assertEqual(self.root.name, "root")

        # check top level tree
        self.assertIsNotNone(self.tree0.parent)
        self.assertEqual(self.tree0.parent, self.root)
        self.assertTrue(self.tree0.items)
        # 2 sub-trees and 1 leaf
        self.assertEqual(len(self.tree0.items), 3)

        # check the leaf item of the top level tree
        self.assertEqual(self.item0.parent, self.tree0)
        self.assertEqual(self.item0.name, "item0.tar.gz")

        # check the populated sub-tree on the "left"
        self.assertEqual(self.tree10.parent, self.tree0)
        self.assertEqual(len(self.tree10.items), 2)
        self.assertIn(self.item100, self.tree10.items)
        self.assertIn(self.item101, self.tree10.items)

        # check the unpopulated sub-tree on the "right"
        self.assertEqual(self.tree11.parent, self.tree0)
        self.assertEqual(len(self.tree11.items), 0)

    def item_path_url_test(self):
        """Check that the item path and URL generation works correctly"""
        # test the top level tree item
        self.assertEqual(self.item0.get_path(), ["level0"])
        self.assertEqual(self.item0.get_url(), os.path.join(URL_PREFIX, "level0", "item0.tar.gz"))

        # test the sub-tree items
        self.assertEqual(self.item100.get_path(), ["level0", "level10"])
        self.assertEqual(self.item100.get_url(), os.path.join(URL_PREFIX, "level0", "level10", "item100.tar.gz"))
        self.assertEqual(self.item101.get_path(), ["level0", "level10"])
        self.assertEqual(self.item101.get_url(), os.path.join(URL_PREFIX, "level0", "level10", "item101.tar.gz"))
