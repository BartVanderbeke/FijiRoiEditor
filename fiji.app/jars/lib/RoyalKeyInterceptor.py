# A Jython class to intercept key presses in the kingdom of ImageJ,
# allowing you to define your own noble key-to-action mappings.

from java.awt import KeyboardFocusManager
from java.awt.event import KeyEvent
from java.awt import KeyEventDispatcher
from ij import IJ

class RoyalKeyInterceptor(KeyEventDispatcher):
    """
    RoyalKeyInterceptor

    A humble servant to intercept key events,
    shielding the kingdom of Fiji from undesired keystrokes.

    Usage:

        interceptor = RoyalKeyInterceptor({
            KeyEvent.VK_ESCAPE: (lambda: print("Escape intercepted!"),None, True),
            KeyEvent.VK_DELETE: (lambda: print("Delete intercepted!"),None,, True)
        })
        interceptor.install()

    Notes:
        - Each mapping is a tuple: (action, argument,should_block)
          where 'action' is a callable (e.g. a lambda function),
          and 'should_block' is True to prevent Fiji from handling the key,
          and argument is an argument for the called function
          or False to let it pass through after your custom action.
    """

    def __init__(self,gvars, mapping=None):
        """
        mapping: dict of keyCode -> (callable, should_block)
        Example: {KeyEvent.VK_ESCAPE: (my_function, True)}
        """
        self.mapping = mapping if mapping else {}
        self.installed = False
        self.gvars=gvars

    def dispatchKeyEvent(self, event):
        if event.getID() != KeyEvent.KEY_PRESSED:
            return False

        key = event.getKeyCode()
        if key in self.mapping:
            action,argument ,should_block = self.mapping[key]
            try:
                action(argument)
            except Exception as ex:
                IJ.log("Error while executing action for key: "+ str(key))
            return should_block  # True to block, False to let through

        return False  # All other keys pass silently through the court

    def install(self):
        """
        Summon the interceptor to stand guard over key presses.
        Call this once to begin intercepting.
        """
        if not self.installed:
            KeyboardFocusManager.getCurrentKeyboardFocusManager().addKeyEventDispatcher(self)
            self.installed = True

    def uninstall(self):
        """
        Relieve the interceptor from its duty.
        Call this to stop intercepting keys.
        """
        if self.installed:
            KeyboardFocusManager.getCurrentKeyboardFocusManager().removeKeyEventDispatcher(self)
            self.installed = False

# from java.awt.event import KeyEvent

# interceptor = RoyalKeyInterceptor({
    # KeyEvent.VK_ESCAPE: (lambda x: print("Escape hath been caught!"),None, True),
    # KeyEvent.VK_DELETE: (lambda x: print("Delete intercepted and tamed."),None, True)
# })
# interceptor.install()

