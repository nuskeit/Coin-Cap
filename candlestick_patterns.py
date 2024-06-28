from enum import Enum
from decimal import Decimal

class CandleStickType:
  UNIDENTIFIED = "UNIDENTIFIED"

  LONG = "BULLISH_LONG"
  REGULAR = "BULLISH_REGULAR"
  SHORT = "BULLISH_SHORT"
  MARUBOZU = "BULLISH_MARUBOZU"
  CLOSING_MARUBOZU = "BULLISH_CLOSING_MARUBOZU"
  OPENING_MARUBOZU = "BULLISH_OPENING_MARUBOZU"
  SPINNING_TOPS = "BULLISH_SPINNING_TOPS"
  HAMMER = "BULLISH_HAMMER"
  HANGING_MAN = "HANGING_MAN"
  INVERTED_HAMMER = "BULLISH_INVERTED_HAMMER"
  SHOOTING_STAR = "SHOOTING_STAR"

  class BULLISH:
    BULLISH = "BULLISH"
    LONG = "BULLISH_LONG"
    REGULAR = "BULLISH_REGULAR"
    SHORT = "BULLISH_SHORT"
    MARUBOZU = "BULLISH_MARUBOZU"
    CLOSING_MARUBOZU = "BULLISH_CLOSING_MARUBOZU"
    OPENING_MARUBOZU = "BULLISH_OPENING_MARUBOZU"
    SPINNING_TOPS = "BULLISH_SPINNING_TOPS"
    HAMMER = "BULLISH_HAMMER"
    INVERTED_HAMMER = "BULLISH_INVERTED_HAMMER"

  class BEARISH:
    BEARISH = "BEARISH"
    LONG = "BEARISH_LONG"
    REGULAR = "BEARISH_REGULAR"
    SHORT = "BEARISH_SHORT"
    MARUBOZU = "BEARISH_MARUBOZU"
    CLOSING_MARUBOZU = "BEARISH_CLOSING_MARUBOZU"
    OPENING_MARUBOZU = "BEARISH_OPENING_MARUBOZU"
    SPINNING_TOPS = "BEARISH_SPINNING_TOPS"
    HANGING_MAN = "BEARISH_HANGING_MAN"
    SHOOTING_STAR = "BEARISH_SHOOTING_STAR"

  class FLAT:
    DOJI = "DOJI"
    LONG_LEGGED_DOJI = "LONG_LEGGED_DOJI"
    CROSS_DOJI = "CROSS_DOJI"
    INVERTED_CROSS_DOJI = "INVERTED_CROSS_DOJI"
    DRAGONFLY_DOJI = "DRAGONFLY_DOJI"
    SPINNING_TOPS = "SPINNING_TOPS"
    GRAVESTONE_DOJI = "GRAVESTONE_DOJI"

cst = CandleStickType()

def identifyCandlestickPattern(o, h, l, c, marketLow, marketHigh, bigCandleRatio=Decimal(10)):
  # Settings:
  DEBUG_MODE = False
  RESOLUTION_MODE = "REL" # REL or ABS
  BALDNESS_TOLERANCE = Decimal(0.5) # Tolerance for assuming close to nothing, in %
  
  # marketLow and marketHigh are the real market values under analysis
  # bigCandleRatio is the % of marquet area

  # First identify the base parts or a candlestick
  # if the cs is bullish, the body is positive (> 0) and if it's bearish, negative (< 0)

  # more_than_this_is_long is adjusted by the min/max of the area being analyzed
  # and what is the ratio that tells a long from a regular body
  if marketHigh == None or marketLow == None:
    return cst.UNIDENTIFIED

  marketSize = marketHigh - marketLow
  
  if marketSize == None:
    return cst.UNIDENTIFIED
  # LARGE
  more_than_this_is_long = marketSize / bigCandleRatio
  # TINY
  less_than_this_is_tiny = more_than_this_is_long / Decimal(10)
  # SHORT: use with less_than_this_is_tiny (x > less_than_this_is_tiny and x < less_than_this_is_short)
  less_than_this_is_short = more_than_this_is_long / Decimal(2)
  less_than_this_is_none = more_than_this_is_long / Decimal(25)

  # Basic parts of a candlestick
  candle = Decimal(h) - Decimal(l)
  # Body
  body = Decimal(c) - Decimal(o)
  body_abs = abs(body)
  is_bullish = body > Decimal(0)
  is_bearish = not is_bullish
  
  # Enter wick
  enterWick = None
  # Exit wick
  exitWick = None
  # Upper wick
  upperWick = None
  # Lower wick
  lowerWick = None
  
  if body > 0:
    # Enter wick
    enterWick = Decimal(o) - Decimal(l)
    # Exit wick
    exitWick = Decimal(h) - Decimal(c)
    # Upper wick
    upperWick = exitWick
    # Lower wick
    lowerWick = enterWick
  elif body <= 0:
    # Enter wick
    enterWick = Decimal(h) - Decimal(o)
    # Exit wick
    exitWick = Decimal(c) - Decimal(l)
    # Upper wick
    upperWick = enterWick
    # Lower wick
    lowerWick = exitWick
  else:
    return cst.UNIDENTIFIED

  # WICKED PARTS CLASIFICATION
  def isNone(length):
    l = abs(length)
    return l <= less_than_this_is_none

  def isTiny(length):
    l = abs(length)
    return l > less_than_this_is_none and abs(length) <= less_than_this_is_tiny

  def isShort(length):
    l = abs(length)
    return l > less_than_this_is_tiny and l <= less_than_this_is_short

  def isRegular(length):
    l = abs(length)
    return l > less_than_this_is_short and l <= more_than_this_is_long

  def isLong(length):
    return abs(length) > more_than_this_is_long


  if isNone(body_abs) :
    body_to_candle = body_abs * Decimal(99.7) 
    leg_difference_ratio_lo = Decimal(1.1)
    leg_difference_ratio_hi = Decimal(1.2)
    if upperWick + lowerWick > body_to_candle :
      if isNone(upperWick) and not isNone(lowerWick) :
        return cst.DRAGONFLY_DOJI
      if isNone(lowerWick) and not isNone(upperWick) :
        return cst.GRAVESTONE_DOJI
      return cst.LONG_LEGGED_DOJI
    if lowerWick > upperWick * leg_difference_ratio_lo and lowerWick < upperWick * leg_difference_ratio_hi :
      return cst.CROSS_DOJI
    if upperWick > lowerWick * leg_difference_ratio_lo and upperWick < lowerWick * leg_difference_ratio_hi :
      return cst.INVERTED_CROSS_DOJI
    # If no better option
    return cst.DOJI

  else :
    if is_bullish :
      if enterWick < body_abs and exitWick < body_abs :
        if isNone(enterWick) and isNone(exitWick) :
          return cst.BULLISH.MARUBOZU
        elif isNone(enterWick) :
          return cst.BULLISH.OPENING_MARUBOZU
        elif isNone(exitWick) :
          return cst.BULLISH.CLOSING_MARUBOZU

        if isLong(body_abs) :
          return cst.BULLISH.LONG
        elif isRegular(body_abs) :
          return cst.BULLISH.REGULAR
        else :
          return cst.BULLISH.SHORT

      elif enterWick > body_abs and exitWick < body_abs * Decimal(5) and not isNone(exitWick) :
        return cst.BULLISH.HAMMER
      elif enterWick < body_abs and exitWick > body_abs * Decimal(5) and not isNone(enterWick) :
        return cst.BULLISH.INVERTED_HAMMER

      if enterWick > body_abs * (5) or exitWick > body_abs * Decimal(5) :
        return cst.BULLISH.SPINNING_TOPS

      # if no better option
      return cst.BULLISH.BULLISH

    else : # is bearish
      if enterWick < body_abs and exitWick < body_abs :
        if isNone(enterWick) and isNone(exitWick) :
          return cst.BEARISH.MARUBOZU
        elif isNone(enterWick) :
          return cst.BEARISH.OPENING_MARUBOZU
        elif isNone(exitWick) :
          return cst.BEARISH.CLOSING_MARUBOZU

        if isLong(body_abs) :
          return cst.BEARISH.LONG
        elif isRegular(body_abs) :
          return cst.BEARISH.REGULAR
        else :
          return cst.BEARISH.SHORT

      elif enterWick > body_abs and exitWick < body_abs * Decimal(5) and not isNone(exitWick) :
        return cst.BEARISH.HANGING_MAN
      elif enterWick < body_abs and exitWick > body_abs * Decimal(5) and not isNone(enterWick) :
        return cst.BEARISH.SHOOTING_STAR

      if enterWick > body_abs * Decimal(5) or exitWick > body_abs * Decimal(5) :
        return cst.BEARISH.SPINNING_TOPS

      # if no better option
      return cst.BEARISH.BEARISH

    #   return cst.BEARISH.HANGING_MAN
    #   return cst.BEARISH.SHOOTING_STAR

  return cst.UNIDENTIFIED
