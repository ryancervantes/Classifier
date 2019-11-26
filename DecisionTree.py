#! /usr/bin/python3
"""
File: DecisionTree.py
Author: Ryan Cervantes
"""
import math
from collections import namedtuple


class DecisionTree:

    ###           ###
    # CLASS METHODS #
    ###           ###

    @classmethod
    def fully_classified(cls, examples, classes):
        """
        return true if the current examples are of only one classification
        """
        for c in classes:
            v = cls.plurality_value(examples, c)
            if v == 1:
                return True
        return False

    @classmethod
    def plurality_value(cls, examples, classs):
        """
        produce a plurality value for a give classification
        """
        classifier = lambda x: x.classification == classs
        total = sum(map(lambda x: 1 if classifier(x) else 0, examples))
        return total/len(examples)


    @classmethod
    def plurality(cls, examples, classes):
        p_values = [
            (c, cls.plurality_value(examples, c)) for c in classes
        ]
        return max(p_values, key=lambda x: x[1])[0]
        
    
    @classmethod
    def H(cls, *probs):
        """
        Calculates Entropy H(V) given v0 - vk weights of decisions
        """
        try:
            return -1*sum(map(lambda vk : math.log2(vk)*vk, probs))
        except ValueError:
            return 0


    @classmethod
    def B(cls, q):
        """
        Calculates Entropy H(V) of a boolean variable given a weight
        """
        return cls.H(q, 1-q)


    @classmethod
    def Remainder(cls, examples, A, V, p, n, pos_class_func):
        """
        Will calculate the total entropy remaining for a given set
        given an attribute A and V
        """
        remainder = 0
        for d in V: # over all distinct values of A
            Ek = list(filter(lambda dp: dp[A] == d, examples))
            pk, nk = cls.pos_neg(Ek, pos_class_func)
            partial = 0
            try:
                partial = (pk + nk)/(p + n) * cls.B(pk/(pk + nk))
            except ZeroDivisionError:
                pass
            remainder += partial
        return remainder


    @classmethod
    def Gain(cls, examples, A, V, p, n, pos_class_func):
        """
        Calculates the information gain of the given attribute A
        that has V distinct values.
        """
        return cls.B(p/(p+n)) - cls.Remainder(examples, A, V, p, n, pos_class_func)
    
    @classmethod
    def pos_neg(cls, examples, classifier):
        pos = sum([1 if classifier(dp) else 0 for dp in examples])
        return (pos, len(examples) - pos)
    
    ###              ###
    # INSTANCE METHODS #
    ###              ###
    
    def __init__(self):
        self.p = 0
        self.n = 0
        self.examples = []
        self.classes = [] 
        self.attrs = []
        self._attr_values= {}
        self.classifier = None
    

    def define_positive_class(self, func):
        self.classifier = func


    def define_attributes(self, *specs):
        attr_specifications = {}
        for spec in specs:
            attr_specifications[spec[0]] = spec[1:]
        self._attr_values = attr_specifications


    def load_examples(self, attrs, tuples):
        Example = namedtuple('Example', attrs + ['classification'])
        self.examples.extend(list(map(Example._make, tuples)))
        self.classes.extend(set(map(lambda x: x[-1], tuples)))
        self.tree = None
        self.attrs.extend(attrs)
        self.p, self.n = DecisionTree.pos_neg(self.examples, self.classifier)


    def generate_tree(self, examples, depth=-1):
        def domain(idx):
            return self._attr_values[self.attrs[idx]]

        def _generate(depth, examples, parent_examples, used_attrs):
            DT = DecisionTree
            used = list(used_attrs)
            # if examples is empty then return the majority of the parent
            if not examples:
                return DT.plurality(parent_examples, self.classes)
            # if they're all the same class return that class
            elif DT.fully_classified(examples, self.classes):
                return examples[0].classification
            # if there are no attributes left return majority of everyone
            elif not set(self.attrs) - set(used):
                return DT.plurality(examples, self.classes)
            # We can still generate the Tree
            else:
                # A <- argmax-a E attributes( IMPORTANCE(a, examples) )
                gain = []
                p, n = DT.pos_neg(parent_examples, self.classifier)
                for a in range(0, len(self.attrs)):
                    if self.attrs[a] in used:
                        gain.append(-1)
                    else:
                        gain.append(
                            DT.Gain(examples, a, domain(a),
                                p, n, self.classifier))
                A = gain.index(max(gain))
                children = []
                for vk in domain(A):
                    # exs <- {e : e E examples and e.A = vk}
                    exs = list(filter(lambda dp: dp[A] == vk, examples))
                    # subtree <- DECISION-TREE-LEARNING(exs, attributes - A, examples)
                    if depth == 0:
                        children.append(DT.plurality(examples, self.classes))
                    else:
                        used.append(self.attrs[A])
                        children.append(_generate(depth-1, exs, examples, used))
                branch = tuple([A] + [c for c in children])
                return branch
        self.tree = _generate(depth, examples, examples, [])


    def classify(self, examples):
        def traversify(node):
            attr = self.attrs[node[0]]
            n = {"attr": attr}
            # for each vk where vk in A
            for i in range(len(self._attr_values[attr])):
                # if that branch is taken, go to value it points to
                key = self._attr_values[attr][i]
                # keys zero indexed but nodes are 1 indexed bc node[0] == attr
                if isinstance(node[i+1], tuple):
                    n[key] = traversify(node[i+1])
                else:
                    n[key] = node[i+1]
            return n
        
        def use_classifier(subtree, example):
            feature = subtree["attr"]
            vk = getattr(example, feature)
            # if it is classification return it
            if subtree[vk] in self.classes:
                return subtree[vk]
            # else we recurse down the tree
            else:
                return use_classifier(
                        subtree[vk],
                        example)

        classifier = traversify(self.tree)
        return [use_classifier(classifier, example)
                for example in examples]


    def print_tree(self):
        def traverse(node, lvl=0):
            print('    ' * (lvl - 1), "|---" * (lvl > 0) + str(node[0] + 1))
            for child in node[1:]:
                if child in self.classes:
                    print('    ' * lvl, "|---" + child)
                else:
                    traverse(child, lvl + 1)
        if isinstance(self.tree, tuple):
            traverse(self.tree)
        else:
            print(self.tree)
            

if __name__ == '__main__':
    import sys
    training_set = []
    with open(sys.argv[1], "r") as data:
        training_set = [tuple(dp.strip(" \n").split(" ")) for dp in [l for l in data]]

    Tree = DecisionTree()
    Tree.define_positive_class(lambda dp: dp.classification in ('A'))
    Tree.load_examples(['attr1', 'attr2', 'attr3', 'attr4', 'attr5', 'attr6', 'attr7', 'attr8'], training_set)
    Tree.define_attributes(
            ('attr1', 'True', 'False'),
            ('attr2', 'True', 'False'),
            ('attr3', 'True', 'False'),
            ('attr4', 'True', 'False'),
            ('attr5', 'True', 'False'),
            ('attr6', 'True', 'False'),
            ('attr7', 'True', 'False'),
            ('attr8', 'True', 'False'))
    Tree.generate_tree(Tree.examples)
    Tree.print_tree()
