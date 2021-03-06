# AUTOGENERATED! DO NOT EDIT! File to edit: notation.ipynb (unless otherwise specified).

__all__ = ['expand_hyphen', 'del_dot', 'del_zero', 'get_unique', 'expand_star', 'expand_colon', 'expand_regex',
           'expand_code', 'get_rows']

# Cell
import pandas as pd



# Cell
# function to expand a string like 'K51.2-K53.8' to a list of codes

# Need regex to extract the number component of the input string
import re
from functools import singledispatch

# The singledispach decorator enables us to have the same name, but use
# different functions depending on the datatype of the first argument.
#
# In our case we want one function to deal with a single string input, and
# another to handle a list of strings. It could all be handled in a single
# function using nested if, but singledispatch makes it less messy and more fun!


# Here is the main function, it is just the name and an error message if the
# argument does not fit any of the inputs that wil be allowed

@singledispatch
def expand_hyphen(expr):
  """
  Expands codes expression(s) that have hyphens to list of all codes

  Args:
      expr (str, list or dict): String or list of strings to be expanded

  Returns:
      List of strings or dict with list of strings

  Examples:
      expand_hyphen('C00*-C26*')
      expand_hyphen('b01.1*-b09.9*')
      expand_hyphen('n02.2-n02.7')
      expand_hyphen('c00*-c260')
      expand_hyphen('b01-b09')
      expand_hyphen('b001.1*-b009.9*')
      expand_hyphen(['b001.1*-b009.9*', 'c11-c15'])
  Note:
      Unequal number of decimals in start and end code is problematic.
      Example: C26.0-C27.11 will not work since the meaning is not obvious:
      Is the step size 0.01? In which case C27.1 will not be included, while
      C27.10 will be (and trailing zeros can be important in codes)
  """
  raise ValueError('The argument must be a string or a list')

# register the function to be used if the input is a string
@expand_hyphen.register(str)
def _(expr):
    # return immediately if nothing to expand
    if '-' not in expr:
      return [expr]

    lower, upper = expr.split('-')

    lower=lower.strip()

    # identify the numeric component of the code
    lower_str = re.search("\d*\.\d+|\d+", lower).group()
    upper_str = re.search("\d*\.\d+|\d+", upper).group()
    # note: what about european decimal notation?
    # also note: what if multiple groups K50.1J8.4-etc


    lower_num = int(lower_str.replace('.',''))
    upper_num = int(upper_str.replace('.','')) +1

    if upper_num<lower_num:
      raise ValueError('The start code cannot have a higher number than the end code')

    # remember length in case of leading zeros
    length = len(lower_str)

    nums = range(lower_num, upper_num)

    # must use integers in a loop, not floats
    # which also means that we must multiply and divide to get decimal back
    # and take care of leading and trailing zeros that may disappear
    if '.' in lower_str:
      lower_decimals = len(lower_str.split('.')[1])
      upper_decimals = len(upper_str.split('.')[1])
      if lower_decimals==upper_decimals:
        multiplier = 10**lower_decimals
        codes = [lower.replace(lower_str, format(num /multiplier, f'.{lower_decimals}f').zfill(length)) for num in nums]
      # special case: allow k1.1-k1.123, but not k.1-k2.123 the last is ambigious: should it list k2.0 only 2.00?
      elif (lower_decimals<upper_decimals) & (upper_str.split('.')[0]==lower_str.split('.')[0]):
        from_decimal = int(lower_str.split('.')[1])
        to_decimal = int(upper_str.split('.')[1]) +1
        nums = range(from_decimal, to_decimal)
        decimal_str = '.'+lower.split('.')[1]
        codes = [lower.replace(decimal_str, '.'+str(num)) for num in nums]
      else:
        raise ValueError('The start code and the end code do not have the same number of decimals')
    else:
        codes = [lower.replace(lower_str, str(num).zfill(length)) for num in nums]
    return codes


# register the function to be used if if the input is a list of strings
@expand_hyphen.register(list)
def _(exprs):
  extended = []
  for expr in exprs:
    extended.extend(expand_hyphen(expr))
  return extended

# register the function to be used if if the input is a dict with list of strings
@expand_hyphen.register(dict)
def _(dikt):
  extended = {name: expand_hyphen(exprs) for name, exprs in dikt.items()}
  return extended

# Cell
def del_dot(code):
  if isinstance(code, str):
    return code.replace('.','')
  else:
    codes = [c.replace('.','') for c in code]
  return codes

def del_zero(code, left=True, right=False):
  if isinstance(code, str):
    codes=[code]
  if left:
    codes = [c.lstrip('0') for c in code]
  if right:
    codes = [c.rstrip('0') for c in code]
  if isinstance(code, str):
    codes=codes[0]
  return codes

# Cell
# A function to identify all unique values in one or more columns
# with one or multiple codes in each cell


def get_unique(df, cols=None, sep=None, strip=False):
  """
  List all unique values in one or more columns with one or more values in each cell
  """
  # if no column(s) are specified, find unique values in whole dataframe
  if cols==None:
    cols=df.columns
  # multiple values with seperator in cells
  if sep:
    all_unique=set()

    for col in cols:
      new_unique = set(df[col].str.cat(sep=',').split(','))
      all_unique.update(new_unique)
  # single valued cells
  else:
    values = pd.unique(df[cols].values.ravel('K'))

  # if need to make sure all elements are strings without surrounding spaces
  if strip:
    values=[str(value).strip() for value in values]

  return values

# Cell
# A function to expand a string with star notation (K50*)
# to list of all codes starting with K50

@singledispatch
def expand_star(code, codelist=None):
  """
  Expand expressions with star notation to a list of all values with the specified pattern

  Args:
    expr (str or list): Expression (or list of expressions) to be expanded
    codelist (list) : A list of all codes

  Examples:
    expand_star('K50*', codelist=icd9)
    expand_star('K*5', codelist=icd9)
    expand_star('*5', codelist=icd9)

  """
  raise ValueError('The argument must be a string or a list')

@expand_star.register(str)
def _(code, codelist=None):
  # return immediately if there is nothing to expand
  if '*' not in code:
    return [code]

  start_str, end_str = code.split('*')

  if start_str and end_str:
    codes = {code for code in codelist if (code.startswith(start_str) & code.endswith(end_str))}

  if start_str:
    codes = {code for code in codelist if code.startswith(start_str)}

  if end_str:
    codes = {code for code in codelist if code.endswith(end_str)}

  return sorted(list(codes))

@expand_star.register(list)
def _(code, codelist=None):

  expanded=[]
  for star_code in code:
    new_codes = expand_star(star_code, codelist=codelist)
    expanded.extend(new_codes)

  # uniqify in case some overlap
  expanded = list(set(expanded))

  return sorted(expanded)

# register the function to be used if if the input is a dict with list of strings
@expand_star.register(dict)
def _(dikt):
  extended = {name: expand_star(exprs) for name, exprs in dikt.items()}
  return extended



# Cell
# function to get all codes in a list between the specified start and end code
# Example: Get all codes between K40:L52

@singledispatch
def expand_colon(code, codelist=None):
  raise ValueError('The argument must be a string or a list')

@expand_colon.register(str)
def _(code, codelist=None):
  """
  Expand expressions with colon notation to a list of complete code names
  code (str or list): Expression (or list of expressions) to be expanded
  codelist (list or array) : The list to slice from

  Examples
    K50:K52
    K50.5:K52.19
    A3.0:A9.3

  Note: This is different from hyphen and star notation because it can handle
  different code lengths and different number of decimals

  """
  if ':' not in code:
    return [code]

  startstr, endstr = code.split(':')

  # remove spaces
  startstr = startstr.strip()
  endstr =endstr.strip()

  # find start and end position
  startpos = codelist.index(startstr)
  endpos = codelist.index(endstr) + 1

  # slice list
  expanded = codelist[startpos:endpos+1]

  return expanded


@expand_colon.register(list)
def _(code, codelist=None, regex=False):
  expanded=[]

  for cod in code:
    new_codes = expand_colon(cod, codelist=codelist)
    expanded.extend(new_codes)

  return expanded
# register the function to be used if if the input is a dict with list of strings
@expand_colon.register(dict)
def _(dikt):
  extended = {name: expand_colon(exprs) for name, exprs in dikt.items()}
  return extended

# Cell

# Return all elements in a list that fits a regex pattern

@singledispatch
def expand_regex(code, codelist):
  raise ValueError('The argument must be a string or a list of strings')

@expand_regex.register(str)
def _(code, codelist=None):
  code_regex = re.compile(code)
  expanded = {code for code in codelist if code_regex.match(code)}
  # uniqify
  expanded = list(set(expanded))
  return expanded

@expand_regex.register(list)
def _(code, codelist):
  expanded=[]

  for cod in code:
    new_codes = expand_regex(cod, codelist=codelist)
    expanded.extend(new_codes)

  # uniqify in case some overlap
  expanded = sorted(list(set(expanded)))

  return expanded
# register the function to be used if if the input is a dict with list of strings
@expand_regex.register(dict)
def _(dikt):
  extended = {name: expand_regex(exprs) for name, exprs in dikt.items()}
  return extended

# Cell
@singledispatch
def expand_code(code, codelist=None,
                hyphen=True, star=True, colon=True, regex=False,
                drop_dot=False, drop_leading_zero=False,
                sort_unique=True):
  raise ValueError('The argument must be a string or a list of strings')

@expand_code.register(str)
def _(code, codelist=None,
      hyphen=True, star=True, colon=True, regex=False,
      drop_dot=False, drop_leading_zero=False,
      sort_unique=True):
  #validating input
  if (not regex) and (':' in code) and (('-' in code) or ('*' in code)):
    raise ValueError('Notation using colon must start from and end in specific codes, not codes using star or hyphen')

  if regex:
    codes = expand_regex(code, codelist=codelist)
    return codes

  if drop_dot:
    code = del_dot(code)

  codes=[code]

  if hyphen:
    codes=expand_hyphen(code)
  if star:
    codes=expand_star(codes, codelist=codelist)
  if colon:
    codes=expand_colon(codes, codelist=codelist)

  if sort_unique:
    codes = sorted(list(set(codes)))

  return codes

@expand_code.register(list)
def _(code, codelist=None, hyphen=True, star=True, colon=True, regex=False,
      drop_dot=False, drop_leading_zero=False,
      sort_unique=True):

  expanded=[]

  for cod in code:
    new_codes = expand_code(cod, codelist=codelist, hyphen=hyphen, star=star, colon=colon, regex=regex, drop_dot=drop_dot, drop_leading_zero=drop_leading_zero)
    expanded.extend(new_codes)

  # uniqify in case some overlap
  expanded = list(set(expanded))

  return sorted(expanded)

@expand_code.register(dict)
def _(code, codelist=None, hyphen=True, star=True, colon=True, regex=False,
      drop_dot=False, drop_leading_zero=False,
      sort_unique=True):
  expanded = {name: expand_code(cod, codelist=codelist,
                                hyphen=hyphen,
                                star=star,
                                colon=colon,
                                regex=regex,
                                drop_dot=drop_dot,
                                drop_leading_zero=drop_leading_zero)
              for name, cod in dikt.items()}
  return expanded


# Cell
# mark rows that contain certain codes in one or more colums
def get_rows(df, codes, cols=None, sep=None, pid='pid', expand=False, codebook=None):
  """
  Make a boolean series that is true for all rows that contain the codes

  Args
    df (dataframe or series): The dataframe with codes
    codes (str, list, set, dict): codes to be counted
    cols (str or list): list of columns to search in
    sep (str): The symbol that separates the codes if there are multiple codes in a cell
    pid (str): The name of the column with the personal identifier

  """

  # string as input for single codes is allowed
  # but then must make it a list
  if isinstance(codes, str):
    codes = [codes]

  # same for cols
  # must be a list sine we may loop over it
  if not isinstance(cols, list):
    cols = [cols]

  if any(notation in ''.join(cols) for notation in '*-:'):
      cols=expand_cols(cols)


  if expand:
     # start with special case. for speed:  endstar notation that does not require expansion
     # (does not require making a list of unique values)
     if any(code.endswith('*') for code in codes):
       star_codes=[code for code in codes if code.endswith('*')]
       codes=[code for code in codes if code not in star_codes]

       #if codes have both star and hyphen notation
       star_codes=expand_hyphen(star_codes)

       #get the rows!
       endstar_rows=_get_rows_endstar(df=df, codes=star_codes, cols=cols, sep=sep)

       # return rows right away if there are no other codes to be checked
       if len(codes)==0:
         return endstar_rows

     # continue with all other codes
     # check if any codes need expansion
     if any(notation in ''.join(codes) for notation in '*-:'):
       codes=expand_codes(codes)

  # approach depends on whether we have multi-value cells or not
  # if sep exist, then have multi-value cells
  if sep:
    # have multi-valued cells
    codes = [rf'\b{code}\b' for code in codes]
    codes_regex = '|'.join(codes)

    # starting point: no codes have been found
    # needed since otherwise the function might return None if no codes exist
    rows = pd.Series(False*len(df),index=df.index)

   # loop over all columns and mark when a code exist
    for col in cols:
      rows=rows | df[col].str.contains(codes_regex, na=False)

  # if not multi valued cells
  else:
    mask = df[cols].isin(codes)
    rows = mask.any(axis=1)

  if 'endstar_rows' in locals():
    rows=rows | endstar_rows

  return rows

# Internal Cell
  def _get_rows_endstar(df, codes, cols, sep=None):
    """
    Returns rows with codes that starts with a given value(s) in one or
    more columns, with one or more values in each column

    Note: special function for the special (but common) case when the user
    wants to pick codes that start with a given string
    """
    codes=[code.strip('*') for code in codes]

    if (sep is None) & (len(codes)==1):
      col=cols[0]
      code=codes[0]
      rows = df[col].str.startswith(code, na=False)
      for col in cols[1:]:
        rows = rows | df[col].str.startswith(code, na=False)

    else:
      regex_list=[rf'\b{code}' for code in codes] #should triple check regex ...
      codes_regex='|'.join(regex_list)

      col=cols[0]
      rows = df[col].str.contains(codes_regex, na=False)

      for col in cols[1:]:
        rows = rows | df[col].str.contains(codes_regex, na=False)

    return rows
