##
#    Project: CometSound - A music player written in Python 
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010-2011 Andrea Bernardini
#    License: GPL-2+
#
#    This file is part of CometSound.
#
#    CometSound is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 2 of the License, or
#    (at your option) any later version.
#
#    CometSound is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with CometSound.  If not, see <http://www.gnu.org/licenses/>.
##

swap = 1
ok = -1
equal = 0

def sortNameFunc(model, iter1, iter2, data = 0):
    """Sorting algorithm for treeview's rows"""
    try:
        value1 = model.get_value(iter1, data).lower()
        value2 = model.get_value(iter2, data).lower()
    except:
        value1 = None
        value2 = None
    row1Isfile = model.get_value(iter1, 8) != ''
    row2Isfile = model.get_value(iter2, 8) != ''
    if value1 == value2:
        if data == 4:
            return sortNumFunc(model, iter1, iter2, 1)
        else:
            return equal
    if not row1Isfile and row2Isfile:
        return ok
    elif not row1Isfile and not row2Isfile:
        sortedRowList = [value1, value2]
        sortedRowList.sort()   
        if sortedRowList == [value1, value2]:
            return ok
        else:
            return swap 
    elif row1Isfile and not row2Isfile:
        return swap
    elif row1Isfile and row2Isfile:
        sortedRowList = [value1, value2]
        sortedRowList.sort()   
        if sortedRowList == [value1, value2]:
            return ok
        else:
            return swap
    
def sortNumFunc(model, iter1, iter2, data):
    """Sorting algorithm for Num column's rows"""
    value1 = model.get_value(iter1, data)
    value2 = model.get_value(iter2, data)
    if type(value1).__name__ == 'str' and value1 != '':
        try:
            row1 = int(value1.split('/')[0])
        except:
            row1 = 0
    else:
        row1 = 0
    if type(value2).__name__ == 'str'and value2 != '':
        try:
            row2 = int(value2.split('/')[0])
        except:
            row2 = 0
    else:
        row2 = 0       
    if row1 == row2:
        return equal
    if row1 < row2:
        return ok
    elif row1 > row2:
        return swap
    return equal