import unittest
import os

from base import ItemTreeRoot, ItemTree, Leaf, Items

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
        self.assertEqual(tree.items.items, [])
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
        tree10.items.add(item100)
        tree10.items.add(item101)
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
        self.assertEqual(self.root.items, [self.tree0])
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


class ItemsTest(unittest.TestCase):

    def length_test(self):
        # empy items should have length of 0
        items = Items()
        self.assertEqual(len(items), 0)

        # check container instantiation from a list of items
        root = ItemTreeRoot(name="top_level")
        item1 = Leaf(name="item1", parent=root)
        item2 = Leaf(name="item2", parent=root)
        tree1 = ItemTree(name="tree1", parent=root)
        items = Items(items=[item1, item2, tree1])

        # our testing items contain 3 items
        self.assertEqual(len(items), 3)
        # check that lenght respects item removal
        items.remove("item1")
        self.assertEqual(len(items), 2)
        items.remove("tree1")
        # clearing should result in zero length
        self.assertEqual(len(items), 1)
        items.clear()
        self.assertEqual(len(items), 0)
        # adding items should increase lenght
        root = ItemTreeRoot(name="top_level")
        foo = Leaf(name="foo", parent=root)
        bar = Leaf(name="bar", parent=root)
        items.add(foo)
        self.assertEqual(len(items), 1)
        items.clear()
        items.add_items([foo, bar])
        self.assertEqual(len(items), 2)

    def in_test(self):
        root = ItemTreeRoot(name="top_level")
        item1 = Leaf(name="item1", parent=root)
        items = Items(items=[item1])
        # stuff thats inside should return True
        self.assertTrue(item1 in items)
        self.assertTrue(item1.name in items)
        self.assertTrue("item1" in items)
        # stuff that is not inside should return False
        self.assertFalse(root in items)
        self.assertFalse("foo" in items)
        self.assertFalse(None in items)
        self.assertFalse(1234 in items)
        self.assertFalse(items in items)

    def get_test(self):
        root = ItemTreeRoot(name="top_level")
        item1 = Leaf(name="item1", parent=root)
        item2 = Leaf(name="item2", parent=root)
        items = Items(items=[item1, item2])
        self.assertEqual(items.get("item1").name, "item1")
        self.assertEqual(items.get("item1"), item1)
        self.assertEqual(items.get("item2").name, "item2")
        self.assertEqual(items.get("item2"), item2)
        self.assertIsNone(items.get("foo"), None)

    def pop_test(self):
        root = ItemTreeRoot(name="top_level")
        item1 = Leaf(name="item1", parent=root)
        item2 = Leaf(name="item2", parent=root)
        items = Items(items=[item1, item2])
        self.assertEqual(items.pop("item1"), item1)
        self.assertEqual(items.pop("item2"), item2)
        with self.assertRaises(KeyError):
            items.pop("item1")
            items.pop("item2")
            items.pop("foo")

    def name_change_test(self):
        root = ItemTreeRoot(name="top_level")
        tree = ItemTree(name="top_level", parent=root)
        item1 = Leaf(name="item1", parent=tree)
        item2 = Leaf(name="item2", parent=tree)
        tree.items.add_items([item1, item2])

        # check if the items were correctly added
        self.assertEqual(tree.items.get("item1").name, "item1")
        self.assertEqual(tree.items.get("item2").name, "item2")

        # change the name of the first item
        tree.items.get("item1").name = "item11"
        self.assertEqual(tree.items.get("item11").name, "item11")
        self.assertTrue("item11" in tree.items)

        # check that the old name does not show up anywhere
        self.assertNotEqual(tree.items.get("item11").name, "item1")
        self.assertEqual(tree.items.get("item1"), None)
        self.assertFalse("item1" in tree.items)

        # same thing for the second item, just to be sure :)
        tree.items.get("item2").name = "item22"
        self.assertEqual(tree.items.get("item22").name, "item22")
        self.assertTrue("item22" in tree.items)
        self.assertNotEqual(tree.items.get("item22").name, "item2")
        self.assertEqual(tree.items.get("item2"), None)
        self.assertFalse("item2" in tree.items)
