
def row_duzenleme(s):
    yeni_string = ""
    a = 0
    for i in s:
        yeni_string += i
        if a == 122:
            yeni_string += "\n"
            a = 0
        a = a+1
    return yeni_string

print(row_duzenleme("asasdadqe qweqwadaw asdaw dasda wd asda dasfdsdfaas asasd asd asd asdasd asd asd asd asd ad asdasdasfa"))
