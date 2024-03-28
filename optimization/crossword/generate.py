from copy import copy
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains.keys() :
            domain_copy=copy(self.domains[var])
            for word in domain_copy:
                if len(word)!=var.length :
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        if self.crossword.overlaps[x, y] is None:
            return False
        x_overlap1, y_overlap1 = self.crossword.overlaps[x, y]
        if x_overlap1 is None:
            return False

        revised = False
        x_words = set(self.domains[x])  # Create a separate copy for removals
        y_words = self.domains[y]

        for x_word in copy(self.domains[x]):
            matched_value=False
            for y_word in y_words:
                if x_word[x_overlap1] == y_word[y_overlap1]:
                    matched_value=True
                    break
            if matched_value ==True:
                continue
            else :
                self.domains[x].remove(x_word)
                revised=True
        
        return revised
    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None :
            variables_queue=[ ]
            for x in self.domains.keys():
                for y in self.crossword.neighbors(x):
                    if self.crossword.overlaps[x, y] is not None:
                        variables_queue.append((x,y))

            while len(variables_queue) > 0 :
                x,y=variables_queue.pop(0)
                if self.revise(x,y) ==True:
                    if len(self.domains[x])==0:#no available word to compare with means probllem unsolvable
                        return False
                    new_arcs=[ (x,z) for z in self.crossword.neighbors(x) if z!=y ]
                    for arc in new_arcs :
                        variables_queue.append(arc)
            return True
        variables_queue=arcs
        
        while len(variables_queue) > 0 :
                x,y=variables_queue.pop(0)
                if self.revise(x,y) ==True:
                    if len(self.domains[x])==0:#no available word to compare with means probllem unsolvable
                        return False
                    new_arcs=[ (x,z) for z in self.crossword.neighbors(x) if z!=y ]
                    for arc in new_arcs :
                        variables_queue.append(arc)    
                        
        return True
    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for x in self.domains.keys():
            if x not in assignment:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        
        #check no doubles in assigenement because every words is used once:
        words_used=[]
        for var in assignment.keys():
            if assignment[var] in words_used :
                return False
            words_used.append(assignment[var])
        #check length of word assigned with var length :
        for var in assignment.keys() :
            if var.length !=len(assignment[var]):
                return False
        
        # check for conflict
        for var in assignment.keys():
            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    x,y=self.crossword.overlaps[var,neighbor]
                    
                    if assignment[var][x]!=assignment[neighbor][y]:
                        return False
        return True
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        values=dict() #words and their count
        for word in self.domains[var]:
            values[word]=0
        neighbors=self.crossword.neighbors(var)
        for neighbor in neighbors :
            x,y=self.crossword.overlaps[var,neighbor]
            for word in self.domains[var]:
                for word_neighbor in self.domains[neighbor]:
                    if word[x]!=word_neighbor[y]:
                        values[word]+=1
        return sorted(values.keys(),key=lambda x :values[x])        
    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        remaining=[]
        for x in self.domains.keys():
            if x not in assignment :
                remaining.append(x)
            
        return min(remaining,key=lambda x:len(self.order_domain_values(x,assignment)))

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var=self.select_unassigned_variable(assignment)
        for word in self.order_domain_values(var,assignment):
            if len(word)==var.length:
                assignment_copy=copy(assignment)
                assignment_copy[var]=word
                result=self.backtrack(assignment_copy)
                if self.consistent(result)==True:
                    return result
        return None   


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
