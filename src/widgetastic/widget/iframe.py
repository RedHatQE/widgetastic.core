# -*- coding: utf-8 -*-
from .base import View


class IFrameView(View):
    """BlaBla

    """
    FRAME = None

    def __init__(self, parent, logger=None, **kwargs):
        View.__init__(self, parent, logger=logger, **kwargs)

    # def child_widget_accessed(self, widget):
    #     # self.browser.switch_to_main_frame()
    #     self.browser.switch_to_frame(self.FRAME)

