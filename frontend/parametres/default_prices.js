var default_prices = {
    "tgb" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Tuborg Guld/Gold"},
    "wih" : {"initial_price" : 67, "krach_price" : 22.33, "full_name":"Windy Hill"},
    "166" : {"initial_price" : 57, "krach_price" : 19, "full_name":"1664"},
    "pul" : {"initial_price" : 62, "krach_price" : 20.67, "full_name":"Pulp Art"},
    "jrl" : {"initial_price" : 67, "krach_price" : 22.33, "full_name":"Japanese Rice Lager"},
    "seh" : {"initial_price" : 62, "krach_price" : 20.67, "full_name":"Special Effects Hoppy Lager"},
    "swi" : {"initial_price" : 62, "krach_price" : 20.67, "full_name":"Stonewall Inn IPA"},
    "dab" : {"initial_price" : 57, "krach_price" : 19, "full_name":"Double Ambrée"},
    "gbl" : {"initial_price" : 57, "krach_price" : 19, "full_name":"Grimbergen Blonde"},
    "jui" : {"initial_price" : 62, "krach_price" : 20.67, "full_name":"Juicy IPA"},
    /*"yak" : {"initial_price" : 62, "krach_price" : 20.67, "full_name":"Yakima IPA"},
    "bla" : {"initial_price" : 57, "krach_price" : 19, "full_name":"Blanc"},
    "bur" : {"initial_price" : 67, "krach_price" : 22.33, "full_name":"Burst"},
    "cla" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Classic"},
    "gro" : {"initial_price" : 39, "krach_price" : 13, "full_name":"Grøn"},
    "hel" : {"initial_price" : 54, "krach_price" : 18, "full_name":"Hell"},
    "pil" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Pilsner"},
    "ocl" : {"initial_price" : 46, "krach_price" : 15.33, "full_name":"Original Czech Lager"},
    "bvd" : {"initial_price" : 49, "krach_price" : 16.33, "full_name":"Budweiser Budvar / Czechvar DARK"},
    "dar" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Dark"},
    "pre" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Premium"},
    "haz" : {"initial_price" : 64, "krach_price" : 21.33, "full_name":"Hazy Jane"},
    "pun" : {"initial_price" : 64, "krach_price" : 21.33, "full_name":"Punk IPA"},
    "kol" : {"initial_price" : 54, "krach_price" : 18, "full_name":"Kölsch"},
    "epa" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"EPA"},
    "sto" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Stout"},
    "bwe" : {"initial_price" : 54, "krach_price" : 18, "full_name":"Benediktiner Weissbier"},
    "weo" : {"initial_price" : 59, "krach_price" : 19.67, "full_name":"Weisse Original"},
    "wei" : {"initial_price" : 44, "krach_price" : 14.67, "full_name":"Weizen"},
    "tap" : {"initial_price" : 67, "krach_price" : 22.33, "full_name":"Tap 7 Original"},
    */
}

color_index = 0
number_of_drinks =  Object.keys(default_prices).length
for(let i in default_prices){
    if(!default_prices[i]["colour"]){
        default_prices[i]["colour"] = "hsl(" + Math.ceil(color_index * 360 / (number_of_drinks+1)) + ", 90%, 60%)";
    }
    color_index += 1
}
