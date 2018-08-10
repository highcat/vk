# -*- coding: utf-8 -*-
BEELINE_CODES = ['903', '905', '906', '909', '951', '953', '960', '961', '962', '963', '964', '965', '966', '967', '968']
from xlrd import open_workbook
from xlutils.copy import copy
for FILE in [
        "/home/highcat/Dropbox/Vkusnyan/SMS_from_slava/100_Давние__ready.xls",
        "/home/highcat/Dropbox/Vkusnyan/SMS_from_slava/100_Недавние__ready.xls",
        "/home/highcat/Dropbox/Vkusnyan/SMS_from_slava/100_Старые__ready.xls",
]:
    rb = open_workbook(FILE)
    wb = copy(rb)
    s_read = rb.sheet_by_index(0)
    s_write = wb.get_sheet(0)
    for row_num in xrange(99999):
        try:
            v = s_read.cell(row_num, 1).value
        except IndexError:
            break
        v = str(int(v))
        beeline = False
        for b in BEELINE_CODES:
            if v.startswith('7'+b):
                beeline = True
        print v, 'beeline' if beeline else ''
        if beeline:
            s_write.write(row_num, 0, '1')
    wb.save(FILE)
