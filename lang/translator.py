from lang.spek.ast import *


class Translator(abc.ABC):
    """
    A translator translates an AST into a target language.
    """

    @abc.abstractmethod
    def translate(self, node, dec):
        """
        Validates an AST node.
        :param node: The AST node to translate.
        :param dec: A dict mapping AST nodes to decorations.
        :return: The result of the translation, in the target language.
        """
        pass


