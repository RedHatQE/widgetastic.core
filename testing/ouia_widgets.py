from widgetastic.ouia import OUIAGenericView
from widgetastic.ouia import OUIAGenericWidget


class Button(OUIAGenericWidget):
    OUIA_COMPONENT_TYPE = "PF/Button"


class Select(OUIAGenericView):
    OUIA_COMPONENT_TYPE = "PF/Select"

    def choose(self, option):
        el = self.browser.element(self)
        return el.select_option(option)
