class DictionaryIncomplete(Exception):
    """An exception raised during the reconstruction of an object
       from a dictionary when a required dictionary key is missing
    """
    def __init__(self, cls, missing_keys):
        # Call the base class constructor with the parameters it needs
        message = "can't instantiate %s from dict, following keys are missing: %s" % (cls, missing_keys)
        super(DictionaryIncomplete, self).__init__(message)

        # list of required keys missing from the dictionary
        self.missing_keys = missing_keys


class MissingParent(Exception):
    """An exception raised during the reconstruction of an object
       from a dictionary when a required dictionary key is missing
    """
    def __init__(self, cls):
        message = "The class %s needs to have a parent specified." % cls
        super(MissingParent, self).__init__(message)


class MissingURLPrefix(Exception):
    """An exception raised when attempting to download from a tree
       that has no URL prefix set for its root.
    """
    def __init__(self, root):
        message = "Tree root %s has no URL prefix set, can't download leaf." % root
        super(MissingURLPrefix, self).__init__(message)


class Item(object):
    """A base class for all Item tree classes"""

    required_keys = set(["name"])

    @classmethod
    def check_dict_keys(cls, d):
        """Check if the provided dictionary contains all the keys
           needed to properly instantiate this class.
           If one or more of the required keys are missing raise the
           DictionaryIncompleteError exception.
        """
        missing_required_keys = set(cls.required_keys).difference(set(d.keys()))
        if missing_required_keys:
            raise DictionaryIncomplete(cls=cls, missing_keys=missing_required_keys)

    @classmethod
    def from_dict(cls, d):
        cls.check_dict_keys(d)
        return cls(name=d["name"])

    def to_dict(self):
        return {}

    def __init__(self, name, parent=None, items=None):
        self._name = name
        self._parent = parent
        self._items = items

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, items):
        self._items = items


class SubItem(Item):
    """An item that always needs to have a parent."""

    @classmethod
    def from_dict(cls, d, parent=None):
        cls.check_dict_keys(d)
        return cls(name=d["name"], parent=parent)


class ItemTreeRoot(Item):
    """A top level root for an item tree."""

    @classmethod
    def from_dict(cls, d, items=None):
        cls.check_dict_keys(d)
        return cls(
            items = items,
            url_prefix = d.get("url_prefix")
        )

    def __init__(self, name, url_prefix=None, items=None):
        # make sure there is a / at end of the URL prefix
        items = items or []
        Item.__init__(self, name=name, items=items)
        if url_prefix and url_prefix[-1] != "/":
            url_prefix = "%s/" % url_prefix
        self._url_prefix = url_prefix

    @property
    def url_prefix(self):
        return self._url_prefix

    @url_prefix.setter
    def url_prefix(self, prefix):
        # make sure there is a / at end of the URL prefix
        if prefix[-1] != "/":
            prefix = "%s/" % prefix
        self._url_prefix = prefix

    def to_dict(self):
        d = super(ItemTreeRoot, self).to_dict()
        d.update({"url_prefix" : self.url_prefix})
        return d


class ItemTree(SubItem):
    """An item tree, it always has a parent and can contain
       additional items (item trees and/or leafs).
    """

    @classmethod
    def from_dict(cls, d, parent=None, items=None, foo=None):
        cls.check_dict_keys(d)
        # sub items always need to have a parent
        if parent is None:
            raise MissingParent(cls)
        return cls(name=d["name"], parent=parent)

    def __init__(self, name, parent, items=None):
        SubItem.__init__(self, name, parent, items)
        self._name = name
        self._parent = parent
        self._items = items or []

    def to_dict(self):
        return {"name": self.name,
                "items": [i.to_dict() for i in self.items]
                }


class Leaf(SubItem):
    """An item tree leaf"""

    def _get_path(self):
        parent = self.parent
        path_components = []
        # We are in a tree leaf, so recursively reach the
        # tree root by going over all parents and remembering
        # path components when we are at it.
        while parent and parent.parent:
            path_components.insert(0, parent.name)
            parent = parent.parent
        # If parent.parent is None, then it is the tree root,
        # because the tree root has no parent.
        root = parent
        if root.url_prefix is None:
            raise MissingURLPrefix(root=root)
        return path_components, parent

    def get_path(self):
        """Return the path leading from the tree root to the this item,
           excluding the tree root and this item.
        """
        return self._get_path()[0]

    def get_url(self):
        path_components, tree_root = self._get_path()

        url = tree_root.url_prefix
        if url[-1] != "/":
            url = "%s/" % url

        # combine the prefix with the path components and item name
        return "%s%s/%s" % (url, "/".join(path_components), self.name)