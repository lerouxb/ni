class Stack(object):
    """Simple implementation of a Stack datatype based on a list.

    This Stack class is based on a Python list. You can give it an optional
    size. It was made for implementing undo and redo inside Document.

    Parameters:
    size -- Optional number of items that can be in the stack. Elements will
            fall off the start of the stack if this limit is exceeded.

    Methods:
    push  -- add something to the stack
    pop   -- remove and return the last item on the stack
    last  -- get the last element without popping
    clear -- remove all elements from the stack

    """
    def __init__(self, size=None):
        self.size = size
        self.__elements = []

    def push(self, element):
        """Add something to the stack."""
        self.__elements.append(element)

        # if we exceed the size allocation, then just remove elements from the
        # start of the stack
        if self.size and len(self.__elements) > self.size:
            self.__elements = self.__elements[-self.size:]

    def pop(self):
        """Remove and return something from the stack."""
        try:
            return self.__elements.pop()
        except IndexError:
            # hmm. shouldn't we rather throw an exception?
            return None

    def last(self):
        """Get the element at the top of the stack without popping."""

        if self.__elements:
            return self.__elements[-1]
        else:
            # hmm. shouldn't we rather throw an exception?
            return None

    def clear(self):
        """Remove all elements from the stack."""
        self.__elements = []

    def __unicode__(self):
        return unicode(self.__elements)

    def __str__(self):
        return self.__elements.__str__()

    def __repr__(self):
        return self.__elements.__repr__()

    def __len__(self):
        return self.__elements.__len__()

