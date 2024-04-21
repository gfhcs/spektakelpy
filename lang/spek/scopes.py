import abc
from abc import ABC

from lang.spek.ast import Identifier
from lang.spek.data.references import FrameReference
from lang.spek.data.terms import CRef, NewCell, Read, Project, NewCellReference, CString, CNone
from util import check_type


class Scope(ABC):
    """
    Represents a contiguous section of code in which names can be defined.
    """

    def __init__(self, parent):
        """
        Creates a new scope.
        :param parent: The scope inside of which this scope is created. May be None.
        """
        super().__init__()
        self._parent = check_type(parent, Scope, allow_none=True)

    @property
    def parent(self):
        """
        The scope inside of which this one exists. May Be None.
        :return:
        """
        return self._parent

    @abc.abstractmethod
    def declare(self, chain, name, cell, on_error, initialize=True, cellify=False):
        """
        Declares a variable name in this scope.
        This procedure may emit allocation code to the given chain. The type of allocation depends on
        the context and the way the variable is used.
        :param chain: The Chain to which the instructions for allocating the new variable should be appended.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param name: Either a string, or None, in which case an anonymous local variable is allocated on the stack.
        :param cell: Specifies if the name should refer to a heap cell (True), or to a stack frame entry (False).
        :param initialize: Specifies if the newly allocated variable should be initialized by writing to it.
        :param cellify: Specifies if the newly allocated variable should be turned into a cell, preserving any
                        value that is already stored in it.
        :return: A Term that evaluates to a Reference to the newly allocated variable.
        """
        pass

    @abc.abstractmethod
    def retrieve(self, name):
        """
        Retrieves a reference representing the given name, that must be visible in this scope.
        :param name: The name for which to retrieve a reference.
        :return: A Reference object.
        """
        pass

    def __getitem__(self, name):
        return self.retrieve(name)


class LoopScope(Scope):
    """
    A scope encompassing a loop.
    """
    def __init__(self, parent, head_chain, successor_chain):
        """
        Creates a new loop scope.
        :param parent: The scope in which the new one is to be created.
        :param head_chain: The Chain representing the head of the loop.
        :param successor_chain: The Chain representing the instructions following regular exit from the loop.
        """
        super().__init__(parent)
        self._head = head_chain
        self._succ = successor_chain

    @property
    def head_chain(self):
        """
        The Chain representing the head of the loop.
        """
        return self._head

    @property
    def successor_chain(self):
        """
        The Chain representing the instructions following regular exit from the loop.
        """
        return self._succ

    def declare(self, *largs, **kwargs):
        return self.parent.declare(*largs, **kwargs)

    def retrieve(self, name):
        return self.parent.retrieve(name)


class ExceptionScope(Scope):
    """
    A scope encompassing the exception handlers of a try block.
    """
    def __init__(self, parent, exception_reference, finally_chain):
        """
        Creates a new exception scope.
        :param parent: The scope in which the new one is to be created.
        :param exception_reference: A reference pointing to the exception object that was caught.
        :param finally_chain: The Chain representing the finally clause of the try block.
        """
        super().__init__(parent)
        self._exref = exception_reference
        self._finally = finally_chain

    @property
    def exception_reference(self):
        """
        A Reference pointing to the exception object that was caught.
        """
        return self._exref

    @property
    def finally_chain(self):
        """
        The Chain representing the finally clause of the try block.
        """
        return self._finally

    def declare(self, *largs, **kwargs):
        return self.parent.declare(*largs, **kwargs)

    def retrieve(self, name):
        return self.parent.retrieve(name)


class FunctionScope(Scope):
    """
    A scope encompassing a function declaration.
    """
    def __init__(self, parent):
        """
        Creates a new function scope.
        :param parent: The scope in which the new one is to be created.
        """
        super().__init__(parent)
        self._names = dict()
        self._offset = 0

    def declare(self, chain, name, cell, on_error, initialize=True, cellify=False):
        r = CRef(FrameReference(self._offset))
        self._offset += 1
        if cell:
            if initialize:
                chain.append_update(r, NewCell(), on_error)
            if cellify:
                chain.append_update(r, NewCell(Read(r)), on_error)
            r = NewCellReference(r)
        if name is not None:
            self._names[name] = r
        return r

    def retrieve(self, name):
        try:
            return self._names[name]
        except KeyError:
            if self.parent is None:
                raise
            return self.parent.retrieve(name)


class ClassScope(Scope):
    """
    A scope encompassing a class declaration.
    """
    def __init__(self, parent, mdictref):
        """
        Creates a new class scope.
        :param parent: The scope in which the new one is to be created.
        :param mdictref: The reference under which the dictionary of class members is expected.
        """
        super().__init__(parent)
        self._names = dict()
        self._offset = 0
        self._mdictref = mdictref

    def declare(self, chain, name, cell, on_error, initialize=True, cellify=False):
        if name is None:
            # We are declaring a local variable:
            return self.parent.declare(chain, name, cell, on_error, initialize=initialize, cellify=cellify)
        # We are declaring a class member. Extend the member dict:
        r = Project(Read(self._mdictref), CString(name))
        if cell:
            if initialize:
                chain.append_update(r, NewCell(), on_error)
            if cellify:
                chain.append_update(r, NewCell(Read(r)), on_error)
            r = NewCellReference(r)
        else:
            if initialize:
                chain.append_update(r, CNone(), on_error)

        if name is not None:
            self._names[name] = r
        return r

    def retrieve(self, name):
        try:
            return self._names[name]
        except KeyError:
            if self.parent is None:
                raise
            return self.parent.retrieve(name)


class ModuleScope(Scope):
    """
    A scope encompassing an entire module.
    """
    def __init__(self, offset=1):
        """
        Creates a new module scope.
        :param offset: The number of stack variables that this module should assume to have been initialized *before*
                       execution starts.
        """
        super().__init__(None)
        self._names = dict()
        self._offset = offset

    def declare(self, chain, name, cell, on_error, initialize=True, cellify=False):
        if name is None:
            # We are declaring a local variable:
            r = CRef(FrameReference(self._offset))
            self._offset += 1
        else:
            # We are declaring a module member. We know that the module definition code is
            # running under a stack frame that has a namespace dict at offset 0. That object needs to be extended.
            r = Project(Read(CRef(FrameReference(0))), CString(name))
        if cell:
            if initialize:
                chain.append_update(r, NewCell(), on_error)
            if cellify:
                chain.append_update(r, NewCell(Read(r)), on_error)
            r = NewCellReference(r)

        if name is not None:
            self._names[name] = r
        return r

    def retrieve(self, name):
        try:
            return self._names[name]
        except KeyError:
            raise KeyError(f"The name '{name}' is not visible in this module!")


class ScopeStack:
    """
    A stack that represents hierarchies of scopes during translation.
    """

    def __init__(self):
        super().__init__()
        self._entries = []

    def declare(self, chain, name, cell, on_error, **kwargs):
        """
        Declares a variable name in the current scope (i.e. the scope that is at the top of the stack).
        This procedure may emit allocation code to the given chain. The type of allocation depends on
        the context and the way the variable is used.
        :param chain: The Chain to which the instructions for allocating the new variable should be appended.
        :param on_error: The Chain to which control should be transferred if the allocation code fails.
        :param name: Either an AST node, or a string, under which the reference generated by this call can be retrieved
                     later. It may be None, in which case an anonymous local variable is allocated on the stack.
        :param cell: Specifies if the name should refer to a heap cell (True), or to a stack frame entry (False).
        :param kwargs: Arguments to Scope.declare
        :return: A Reference object that represents the newly allocated variable.
        """

        if name is None:
            pass
        elif isinstance(name, str):
            pass
        elif isinstance(name, Identifier):
            name = name.name
        else:
            raise TypeError(f"Cannot declare names for objects of type {type(name)}!")

        return self.top.declare(chain, name, cell, on_error, **kwargs)

    def retrieve(self, name):
        """
        Retrieves the reference that was created for the given name.
        :param name: Either an AST node, or a string, for which self.declare has been called.
        :return: A Reference object.
        """
        try:
            return self.top[name]
        except KeyError:
            if isinstance(name, Identifier):
                return self.top[name.name]
            raise

    def push(self, entry):
        """
        Pushes an entry to the top of the stack.
        :param entry: The entry to push.
        """
        if not (len(self._entries) == 0 or entry.parent is self.top):
            raise ValueError("The parent of the scope to be added must be the current top of the stack!")
        self._entries.append(entry)

    def pop(self):
        """
        Removes the latest entry from the stack.
        :return: The entry that was popped.
        """
        return self._entries.pop()

    @property
    def top(self):
        """
        The entry on the top of the stack.
        """
        return self._entries[-1]

    def __iter__(self):
        entry = self.top
        while entry is not None:
            yield entry
            entry = entry.parent