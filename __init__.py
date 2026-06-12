"""레퍼런스 보드 패키지.

Nuke에서 ``reference_board.main()`` 으로 호출한다.
"""


def main() -> None:
    """레퍼런스 보드 패널을 플로팅 창으로 띄운다."""
    from .main import show_panel
    show_panel()
