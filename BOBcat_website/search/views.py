from django.shortcuts import render
from django.views.generic.edit import CreateView

from mainpage.forms import SearchForm
from mainpage.models import Candidate

from BOBcat_utils.NED_name_resolver import NED_name_resolver
from BOBcat_utils.ra_hms2deg import ra_hms2deg

import re
from decimal import Decimal

def searchpage(request):
    message = ""
    form = SearchForm()
    source_filter_dict = {}
    source_exclude_dict = {}
    model_filter_dict = {}
    model_exclude_dict = {}
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            clean_form_data = form.cleaned_data
            query_name = clean_form_data.get("name")
            query_ra_hms = clean_form_data.get("ra_hms")
            query_ra_deg = clean_form_data.get("ra_deg")
            query_dec_dms = clean_form_data.get("dec_dms")
            query_dec_deg = clean_form_data.get("dec_deg")
            # now in the object cd, you have the form as a dictionary.
            if query_name:
                try:
                    query_NED_name = NED_name_resolver(query_name)
                except:
                    message = "Name provided is not in the NED database.\
                          Try removing the source name and searching based on RA and Dec."
                if not(message):
                    source_filter_dict["NED_name"] = query_NED_name
      
            if query_ra_hms and not(query_ra_deg):
                if (re.findall("^[<>]", query_ra_hms)) and not(" " in query_ra_hms):
                    message = "Please make sure you have a space between the operator and RA value."
                elif (re.findall("^[^<>0123456789+-]", query_ra_hms)):
                    message = "Please make sure your RA value is inputted correctly.\
                        Acceptable search example: 13h05m33.0149s or >= 196.38756"
                elif (len(re.findall("[hms]", query_ra_hms))% 3) != 0:
                    message = "Please make sure you are using hms notation for your RA value, such as 13h05m33.0149s."
                elif (query_ra_hms.count("-") > 1) and ((re.findall("^[-]", query_ra_hms))):
                    query_ra_hms = query_ra_hms.replace(" ", "")
                    range_values = query_ra_hms.split("-")
                    min_val, max_val = ['-'.join(range_values[:2]), '-'.join(range_values[2:])]
                    min_val = str(ra_hms2deg(min_val))
                    max_val = str(ra_hms2deg(max_val))
                    query_ra_deg = min_val + "-" + max_val
                elif (query_ra_hms.count("-") > 1) and ((re.findall("^[^-]", query_ra_hms))):
                    query_ra_hms = query_ra_hms.replace(" ", "")
                    range_values = query_ra_hms.split("-")
                    min_val, max_val = ['-'.join(range_values[:1]), '-'.join(range_values[1:])]
                    min_val = str(ra_hms2deg(min_val))
                    max_val = str(ra_hms2deg(max_val))
                    query_ra_deg = min_val + "-" + max_val
                elif (query_ra_hms.count("-") == 1) and ((re.findall("^[^-<>]", query_ra_hms))):
                    query_ra_hms = query_ra_hms.replace(" ", "")
                    range_values = query_ra_hms.split("-")
                    min_val, max_val = ['-'.join(range_values[:1]), '-'.join(range_values[1:])]
                    min_val = str(ra_hms2deg(min_val))
                    max_val = str(ra_hms2deg(max_val))
                    query_ra_deg = min_val + "-" + max_val
                elif (" " in query_ra_hms):
                    operator, query_ra_hms = query_ra_hms.split(" ")
                    ra_deg = str(ra_hms2deg(query_ra_hms))
                    query_ra_deg = operator + " " + ra_deg
                elif not(" " in query_ra_hms):
                    query_ra_deg = str(ra_hms2deg(query_ra_hms))
                else:
                    message = "Please make sure your RA input has one space between the operator and RA value. \
                             No other spaces should be present. The only operators accepted are: >, >=, <, <=. \
                                 Acceptable search example: 13h05m33.0149s or >= 196.38756"
                

            if query_ra_deg:
                if (re.findall("^[<>]", query_ra_deg)) and not(" " in query_ra_deg):
                    message = "Please make sure you have a space between the operator and RA value."

                elif (re.findall("^[^<>0123456789+-]", query_ra_deg)):
                    message = "Please make sure your RA value is inputted correctly.\
                        Acceptable search example: 13h05m33.0149s or >= 196.38756"
                    
                elif (query_ra_deg.count("-") > 1) and ((re.findall("^[-]", query_ra_deg))):
                    query_ra_deg = query_ra_deg.replace(" ", "")
                    range_values = query_ra_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:2])), Decimal('-'.join(range_values[2:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["ra_deg" + filter_type] = [min_val, max_val]
                elif (query_ra_deg.count("-") > 1) and ((re.findall("^[^-]", query_ra_deg))):
                    query_ra_deg = query_ra_deg.replace(" ", "")
                    range_values = query_ra_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:1])), Decimal('-'.join(range_values[1:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["ra_deg" + filter_type] = [min_val, max_val]
                elif (query_ra_deg.count("-") == 1) and ((re.findall("^[^-<>]", query_ra_deg))):
                    query_ra_deg = query_ra_deg.replace(" ", "")
                    range_values = query_ra_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:1])), Decimal('-'.join(range_values[1:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["ra_deg" + filter_type] = [min_val, max_val]
                elif (" " in query_ra_deg):
                    operator, query_ra_deg = query_ra_deg.split(" ")
                    if operator == ">":
                        filter_type = "__gt"
                    elif operator == ">=":
                        filter_type = "__gte"
                    elif operator == "<":
                        filter_type = "__lt"
                    elif operator == "<=":
                        filter_type = "__lte"
                    else:
                        message = "Please make sure you are using accepted operators only. \
                            The only operators accepted are: >, >=, <, <=."
                    source_filter_dict["ra_deg" + filter_type] = query_ra_deg
                else:
                    try:
                        filter_type = "__range"
                        tol_amt = abs(Decimal(query_ra_deg) * Decimal(0.001))
                        source_filter_dict["ra_deg" + filter_type] = [Decimal(query_ra_deg)-tol_amt,\
                                                                   Decimal(query_ra_deg)+tol_amt]
                    except:
                        message = "Please make sure your RA input has one space between the operator and RA value. \
                                No other spaces should be present. The only operators accepted are: >, >=, <, <=. \
                                   Acceptable search example: 13h05m33.0149s or >= 196.38756"

            # if query_dec_dms and not(query_dec_deg):
            #     if (re.findall("^[<>]", query_dec_dms)) and not(" " in query_dec_dms):
            #         message = "Please make sure you have a space between the operator and Dec value."
            #     elif (re.findall("^[^<>0123456789+-]", query_dec_dms)):
            #         message = "Please make sure your Dec value is inputted correctly.\
            #             Acceptable search example: 13h05m33.0149s or >= 196.38756"
            #     elif (len(re.findall("[dms]", query_dec_dms))% 3) != 0:
            #         message = "Please make sure you are using dms notation for your Dec value, such as 13h05m33.0149s."
            #     elif (query_dec_dms.count("-") > 1) and ((re.findall("^[-]", query_dec_dms))):
            #         query_dec_dms = query_dec_dms.replace(" ", "")
            #         range_values = query_dec_dms.split("-")
            #         min_val, max_val = ['-'.join(range_values[:2]), '-'.join(range_values[2:])]
            #         min_val = str(ra_hms2deg(min_val))
            #         max_val = str(ra_hms2deg(max_val))
            #         query_dec_dms = min_val + "-" + max_val
            #     elif (query_ra_hms.count("-") > 1) and ((re.findall("^[^-]", query_ra_hms))):
            #         query_ra_hms = query_ra_hms.replace(" ", "")
            #         range_values = query_ra_hms.split("-")
            #         min_val, max_val = ['-'.join(range_values[:1]), '-'.join(range_values[1:])]
            #         min_val = str(ra_hms2deg(min_val))
            #         max_val = str(ra_hms2deg(max_val))
            #         query_ra_deg = min_val + "-" + max_val
            #     elif (query_ra_hms.count("-") == 1) and ((re.findall("^[^-<>]", query_ra_hms))):
            #         query_ra_hms = query_ra_hms.replace(" ", "")
            #         range_values = query_ra_hms.split("-")
            #         min_val, max_val = ['-'.join(range_values[:1]), '-'.join(range_values[1:])]
            #         min_val = str(ra_hms2deg(min_val))
            #         max_val = str(ra_hms2deg(max_val))
            #         query_ra_deg = min_val + "-" + max_val
            #     elif (" " in query_ra_hms):
            #         operator, query_ra_hms = query_ra_hms.split(" ")
            #         ra_deg = str(ra_hms2deg(query_ra_hms))
            #         query_ra_deg = operator + " " + ra_deg
            #     elif not(" " in query_ra_hms):
            #         query_ra_deg = str(ra_hms2deg(query_ra_hms))
            #     else:
            #         message = "Please make sure your RA input has one space between the operator and RA value. \
            #                  No other spaces should be present. The only operators accepted are: >, >=, <, <=. \
            #                      Acceptable search example: 13h05m33.0149s or >= 196.38756"


            if query_dec_deg:
                if (re.findall("^[<>]", query_dec_deg)) and not(" " in query_dec_deg):
                    message = "Please make sure you have a space between the operator and Dec value."

                elif (re.findall("^[^<>0123456789+-]", query_dec_deg)):
                    message = "Please make sure your Dec value is inputted correctly.\
                        Acceptable search example: -10d33m19.426s or >= -10.55540"
                    
                elif (query_dec_deg.count("-") > 1) and ((re.findall("^[-]", query_dec_deg))):
                    query_dec_deg = query_dec_deg.replace(" ", "")
                    range_values = query_dec_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:2])), Decimal('-'.join(range_values[2:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["dec_deg" + filter_type] = [min_val, max_val]
                elif (query_dec_deg.count("-") > 1) and ((re.findall("^[^-]", query_dec_deg))):
                    query_dec_deg = query_dec_deg.replace(" ", "")
                    range_values = query_dec_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:1])), Decimal('-'.join(range_values[1:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["dec_deg" + filter_type] = [min_val, max_val]
                elif (query_dec_deg.count("-") == 1) and ((re.findall("^[^-<>]", query_dec_deg))):
                    query_dec_deg = query_dec_deg.replace(" ", "")
                    range_values = query_dec_deg.split("-")
                    range_values =[Decimal('-'.join(range_values[:1])), Decimal('-'.join(range_values[1:]))]
                    range_values.sort()
                    min_val, max_val = range_values
                    filter_type = "__range"
                    source_filter_dict["dec_deg" + filter_type] = [min_val, max_val]
                elif (" " in query_dec_deg):
                    operator, query_dec_deg = query_dec_deg.split(" ")
                    if operator == ">":
                        filter_type = "__gt"
                    elif operator == ">=":
                        filter_type = "__gte"
                    elif operator == "<":
                        filter_type = "__lt"
                    elif operator == "<=":
                        filter_type = "__lte"
                    else:
                        message = "Please make sure you are using accepted operators only. \
                            The only operators accepted are: >, >=, <, <=."
                    source_filter_dict["dec_deg" + filter_type] = query_dec_deg
                else:
                    try:
                        filter_type = "__range"
                        tol_amt = abs(Decimal(query_dec_deg) * Decimal(0.001))
                        source_filter_dict["dec_deg" + filter_type] = [Decimal(query_dec_deg)-tol_amt,\
                                                                   Decimal(query_dec_deg)+tol_amt]
                    except:
                        message = "Please make sure your Dec input has one space between the operator and RA value. \
                                No other spaces should be present. The only operators accepted are: >, >=, <, <=. \
                                   Acceptable search example: -10d33m19.426s or >= -10.55540"
        


            if message:
                return render(request, "search/bad_search.html", {"message": message})

            if len(source_filter_dict) !=0:
                source_search_results = source.objects.filter(**source_filter_dict)
            else:
                message = "Empty search. Please input values into at least one search field."

            if message:
                return render(request, "search/bad_search.html", {"message": message})
            elif len(source_search_results) != 0:
                return render(request, "search/search_results.html", {"search_results": source_search_results})
            else:
                message = "No entries in the BOBcat database match all your search parameters, \
                    please make sure they are correct."
                return render(request, "search/bad_search.html", {"message": message})
                
