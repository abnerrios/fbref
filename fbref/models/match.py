class Match:
  def __init__(self) -> None:
    self.competition = str
    self.home = str
    self.away = str
    self.score = str
    self.date = str
    self.venue = str
  
  def detail(self) -> str:
    """ """
    return f""" 
    =====* {self.competition} *===== 
      ⚽️ {self.date}
      {self.home} X {self.away}
      🏟  {self.venue} #
    """