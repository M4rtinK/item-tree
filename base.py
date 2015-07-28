from threading import RLock

try:
  base_string = basestring  # Python 2
except NameError:
  base_string = str  # Python 3

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


class Item(object):
    """A base class for all Item tree classes"""

    required_keys = set(["name"])

    @classmethod
    def check_dict_keys(cls, item_dict):
        """Check if the provided dictionary contains all the keys
           needed to properly instantiate this class.
           If one or more of the required keys are missing raise the
           DictionaryIncompleteError exception.
        """
        missing_required_keys = set(cls.required_keys).difference(set(item_dict.keys()))
        if missing_required_keys:
            raise DictionaryIncomplete(cls=cls, missing_keys=missing_required_keys)

    @classmethod
    def from_dict(cls, item_dict):
        cls.check_dict_keys(item_dict)
        return cls(name=item_dict["name"])

    def to_dict(self):
        return {}

    def __init__(self, name, parent=None, items=None):
        self._name = name
        self._parent = parent
        self._items = Items(items=items)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        old_name = self._name
        self._name = new_name
        # update name in parents items container, as it is cached
        # for quick membership testing an name -> item retrieval
        if self.parent:  # skip for tree roots
            self.parent.items.update_name(old_name, new_name)

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

    def get_item_for_path(self, path_list):
        """Return item specified by the given path (if any)."""
        if not self.items:
            # empty tree or a leaf
            return None
        else:
            head = path_list[0]
            tail = path_list[1:]
            item = self.items.get(head)
            if item:
                if tail == []:
                    # this is the tree or leaf we want, return it
                    return item
                else:
                    # recurse further down to find the tree/leaf we want
                    return item.get_item(tail)


class SubItem(Item):
    """An item that always needs to have a parent."""

    @classmethod
    def from_dict(cls, item_dict, parent=None):
        cls.check_dict_keys(item_dict)
        return cls(name=item_dict["name"], parent=parent)


class MissingURLPrefix(Exception):
    """An exception raised when attempting to download from a tree
       that has no URL prefix set for its root.
    """
    def __init__(self, root):
        message = "Tree root %s has no URL prefix set, can't download leaf." % root
        super(MissingURLPrefix, self).__init__(message)


class ItemTreeRoot(Item):
    """A top level root for an item tree."""

    @staticmethod
    def get_child_from_dict(child_dict):
        child_items = child_dict.get("items", None)
        if child_items is None:
            return Leaf
        else:
            return ItemTree

    @classmethod
    def from_dict(cls, item_dict):
        cls.check_dict_keys(item_dict)
        items = []
        item_dicts = item_dict.get("items", [])
        for item_dict in item_dicts:
            # instantiate all items we have dicts for
            # NOTE: this is essentially recursive
            items.append(cls.get_child_from_dict(item_dict))
        return cls(
            name = item_dict["name"],
            items = items,
            url_prefix = item_dict.get("url_prefix")
        )

    def __init__(self, name, items=None, url_prefix=None):
        # make sure there is a / at end of the URL prefix
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
        item_dict = super(ItemTreeRoot, self).to_dict()
        item_dict.update({"url_prefix" : self.url_prefix})
        return item_dict


class ItemTree(SubItem):
    """An item tree, it always has a parent and can contain
       additional items (item trees and/or leafs).
       The parent can be either another item tree or an
       item tree root.
    """

    @staticmethod
    def get_child_from_dict(child_dict):
        child_items = child_dict.get("items", None)
        if child_items is None:
            return Leaf
        else:
            return ItemTree

    @classmethod
    def from_dict(cls, item_dict, parent=None, items=None, foo=None):
        cls.check_dict_keys(item_dict)
        # sub items always need to have a parent
        if parent is None:
            raise MissingParent(cls)

        items = []
        item_dicts = item_dict.get("items", [])
        for item_dict in item_dicts:
            # instantiate all items we have dicts for
            # NOTE: this is essentially recursive
            items.append(cls.get_child_from_dict(item_dict))

        return cls(name=item_dict["name"], parent=parent, items=items)

    def to_dict(self):
        item_dict = super(ItemTree, self).to_dict()
        item_dict.update({
            "items": [i.to_dict() for i in self.items.items]
        })
        return item_dict


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

    @property
    def items(self):
        """Leafs don't hold any items."""
        return None

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


class IncorrectItem(Exception):
    """An exception raised when attempting to add an incorrect object
       to the Items container.
    """
    def __init__(self, wrong_item):
        message = "Items without a name property can't be added" \
                  "to the Items container. Name also can't be None." \
                  "Item in question: %s" % wrong_item
        super(IncorrectItem, self).__init__(message)


class IncorrectItemSpec(Exception):
    """An exception raised when and incorrect item specification is provided.
       The item specification needs to be either a string (name of the object)
       or an object with the name property.
    """
    def __init__(self, wrong_spec):
        message = "Item specification needs to be either a string (name of the item)" \
                  "or an Object with the name property, not: %s" % wrong_spec
        super(IncorrectItemSpec, self).__init__(message)


class Items(object):
    """A container for efficiently holding items for a tree.
       It makes sure together with the Item class implementation that
       the item names are consistent with the keys in the internal
       dictionary. This enables quick checking if an object of a given
       name is present in items while keeping tree consistency
       (item name can be changed without the risk of keeping old
        name in keys).
       The container itself also should be thread safe.
    """

    def __init__(self, items=None):
        self._item_dict = {}
        self._item_dict_lock = RLock()
        if items:
            self.add_items(items)

    def __contains__(self, item):
        with self._item_dict_lock:
            if isinstance(item, base_string):
                return item in self._item_dict
            elif hasattr(item, "name"):
                return item.name in self._item_dict

    def __len__(self):
        """Return number of items in the container."""
        with self._item_dict_lock:
            return len(self._item_dict)

    @property
    def items(self):
        """Return an iterable with all items stored in this container."""
        with self._item_dict_lock:
            return self._item_dict.values()

    def get(self, item_name):
        """Get item by name."""
        with self._item_dict_lock:
            return self._item_dict.get(item_name)

    def pop(self, item_spec):
        """Remove an item from the dictionary and return it.

        :raises IncorrectItemSpec: if an incorrect item specification is provided
        :raises KeyError: if the specified item is not in the container
        """
        with self._item_dict_lock:
            if isinstance(item_spec, base_string):
                name = item_spec
            elif hasattr(item_spec, "name"):
                name = item_spec.name
            else:
                raise IncorrectItemSpec(item_spec)

            return self._item_dict.pop(name)

    def remove(self, item_spec):
        """Remove an item from the dictionary.

        :raises IncorrectItemSpec: if an incorrect item specification is provided
        :raises KeyError: if the specified item is not in the container
        """
        with self._item_dict_lock:

            if isinstance(item_spec, base_string):
                name = item_spec
            elif hasattr(item_spec, "name"):
                name = item_spec.name
            else:
                raise IncorrectItemSpec(item_spec)
            del self._item_dict[name]

    def clear(self):
        with self._item_dict_lock:
            self._item_dict.clear()

    def _check_item(self, item):
        """Check if the item has a valid name"""
        name = getattr(item, "name", None)
        if name is None:
            raise IncorrectItem(item)

    def add(self, item):
        with self._item_dict_lock:
            self._check_item(item)
            self._item_dict[item.name] = item

    def add_items(self, items):
        with self._item_dict_lock:
            for item in items:
                self._check_item(item)
                self._item_dict[item.name] = item

    def update_name(self, old_name, new_name):
        """Used by items to update their name in the Items container."""
        with self._item_dict_lock:
            item = self.pop(old_name)
            self._item_dict[new_name] = item
