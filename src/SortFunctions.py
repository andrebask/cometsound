##
#    Project: CometSound - A Music player written in Python 
#    Author: Andrea Bernardini <andrebask@gmail.com>
#    Copyright: 2010 Andrea Bernardini
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

def sortNameFunc(model, iter1, iter2, data):
    """Sorting algorithm for treeview's rows"""
    row1 = model.get_value(iter1, 8)
    row2 = model.get_value(iter2, 8)
    if row1 == '' and row2 !=  '':
        return -1
    elif row1 == '' and row2 ==  '':
        row1 = model.get_value(iter1, 0) 
        row2 = model.get_value(iter2, 0)
        rowList = [row1, row2]
        sortedRowList = [row1, row2]   
        sortedRowList.sort()
        if rowList == sortedRowList:
            return -1
        else:
            return 1        
    elif row1 != '' and row2 ==  '':
        return 1
    else:
        rowList = [row1, row2]
        sortedRowList = [row1, row2]   
        sortedRowList.sort()
        if rowList == sortedRowList:
            return -1
        else:
            return 1     
    
def sortNumFunc(model, iter1, iter2, data):
    """Sorting algorithm for Num column's rows"""
    try:
        row1 = int(model.get_value(iter1, data))
        row2 = int(model.get_value(iter2, data))
    except:
        try:
            row1 = int(model.get_value(iter1, data).split('/')[0])
            row2 = int(model.get_value(iter2, data).split('/')[0])     
        except:
            row1 = model.get_value(iter1, 0) 
            row2 = model.get_value(iter2, 0)
            rowList = [row1, row2]
            sortedRowList = [row1, row2]   
            sortedRowList.sort()
            if rowList == sortedRowList:
                return -1
            else:
                return 1
    if row1 < row2:
        return -1
    elif row1 > row2:
        return 1
    return 0

def sortArtistFunc(model, iter1, iter2, data):
    """Sorting algorithm for treeview's rows"""
    row1 = model.get_value(iter1, 4)
    row2 = model.get_value(iter2, 4)
    if row1 == '' and row2 !=  '':
        return -1
    elif row1 == '' and row2 ==  '':
        row1 = model.get_value(iter1, 0) 
        row2 = model.get_value(iter2, 0)
        rowList = [row1, row2]
        sortedRowList = [row1, row2]   
        sortedRowList.sort()
        if rowList == sortedRowList:
            return -1
        else:
            return 1        
    elif row1 != '' and row2 ==  '':
        return 1
    elif row1 == row2:
        return sortNumFunc(model, iter1, iter2, 1)
    else:
        rowList = [row1, row2]
        sortedRowList = [row1, row2]   
        sortedRowList.sort()
        if rowList == sortedRowList:
            return -1
        else:
            return 1   