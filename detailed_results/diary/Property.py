
class Property:
    def __init__(self, name, lonlat):
        '''
        Construct a bnew hash table with a fixed number of cells equal to the
        parameter "cells", and which yields the value defval upon a lookup to a
        key that has not previously been inserted
        '''
        self.name = name
        self.lonlat = lonlat

    def __repr__(self):
        return 'Property({}, {})'.format(self.name, self.lonlat)

    def __str__(self):
        return '{}, {}'.format(self.name, self.lonlat)
'''

class Meal(models.Model):
    food = models.ForeignKey('Food')
    units = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.now)

    def calories(self):
        return self.food.calories * self.units

    def __repr__(self):
        return 'Meal({}, {}, {})'.format(self.food, self.units, self.timestamp)

    def __str__(self):
        return '{}, {}'.format(self.food.name, self.units)

admin.site.register(Meal)
'''