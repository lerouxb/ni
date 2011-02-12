import gtk


def get_menu_xml():
    return """
<ui>
  <menubar>
    <menu name="FileMenu" action="File">
      <menuitem name="New" action="CreateNewDocument" />
      <menuitem name="Open" action="OpenDocument" />
      <menuitem name="Switch Document" action="SwitchDocument" />
      <separator/>
      <menuitem name="Save" action="SaveDocument" />
      <menuitem name="Save As" action="SaveDocumentAs" />
      <menuitem name="Save All" action="SaveAllDocuments" />
      <separator/>
      <menuitem name="Close" action="CloseDocument" />
      <menuitem name="Close All" action="CloseAllDocuments" />
      <separator/>
      <menuitem name="Quit" action="ExitEditor" />
    </menu>
    <menu name="EditMenu" action="Edit">
      <menuitem name="Undo" action="Undo" />
      <menuitem name="Redo" action="Redo" />
      <separator />
      <menuitem name="Cut" action="CutToClipboard" />
      <menuitem name="Copy" action="CopyToClipboard" />
      <menuitem name="Paste" action="PasteFromClipboard" />
      <menuitem name="Delete" action="DeleteSelection" />
      <separator />
      <menuitem name="Select All" action="SelectAll" />
      <menuitem name="Select None" action="CancelSelection" />
      <separator />
      <menuitem name="Indent" action="Indent" />
      <menuitem name="Unindent" action="Unindent" />
      <separator />
      <menuitem name="Go to Line" action="GoToLine" />
      <separator />
      <menuitem name="Preferences" action="Preferences" />
    </menu>
    <menu name="SearchMenu" action="Search">
      <menuitem name="Find" action="FindorReplace" />
      <menuitem name="Find Next" action="FindNext" />
      <menuitem name="Find Previous" action="FindPrevious" />
    </menu>
    <menu name="ViewMenu" action="View">
      <menuitem name="Toggle Sidebar" action="ToggleSidebar" />
      <menuitem name="Toggle Search Results" action="ToggleSearchResults" />
      <menuitem name="Toggle Line Numbers" action="ToggleLineNumbers" />
      <menuitem name="Toggle Statusbar" action="ToggleStatusbar" />
      <menuitem name="Toggle Right Margin" action="ToggleRightMargin" />
      <separator />
      <menuitem name="Previous Document" action="SwitchToPreviousDocument" />
      <menuitem name="Next Document" action="SwitchToNextDocument" />
      <separator />
      <placeholder name="DocumentList" />
    </menu>
    <menu name="WorkspacesMenu" action="Workspaces">
        <menuitem name="Add Workspace" action="AddWorkspace" />
        <menuitem name="Edit Workspace" action="EditWorkspace" />
        <menuitem name="Clear Cache" action="ClearWorkspaceCache" />
        <separator />
    </menu>
    <menu name="HelpMenu" action="Help">
      <menuitem name="Ni Help" action="NiHelp" />
    </menu>
  </menubar>
</ui>
"""

def get_actions(editor):
    # * The name of the action. Must be specified.
    # * The stock id for the action. Optional with a default value of None
    #   if a label is specified.
    # * The label for the action. Optional with a default value of None if a
    #   stock id is specified.
    # * The accelerator for the action, in the format understood by the
    #   gtk.accelerator_parse() function. Optional with a default value of
    #   None.
    # * The tooltip for the action. Optional with a default value of None.
    # * The callback function invoked when the action is activated. Optional
    #   with a default value of None.
    actions = (
        ('File', None, '_File', None, None, None),
        ('CreateNewDocument', gtk.STOCK_NEW, None, '<ctrl>N', None, editor.action_callback),
        ('OpenDocument', gtk.STOCK_OPEN, None, '<ctrl>O', None, editor.action_callback),
        ('SwitchDocument', None, "S_witch Document", '<ctrl>D', None, editor.action_callback),
        ('SaveDocument', gtk.STOCK_SAVE, None, '<ctrl>S', None, editor.action_callback),
        ('SaveDocumentAs', gtk.STOCK_SAVE_AS, None, '<shift><ctrl>S', None, editor.action_callback),
        ('SaveAllDocuments', None, 'Save A_ll', None, None, editor.action_callback),
        ('CloseDocument', gtk.STOCK_CLOSE, None, '<ctrl>W', None, editor.action_callback),
        ('CloseAllDocuments', None, 'Clos_e All', None, None, editor.action_callback),
        ('ExitEditor', gtk.STOCK_QUIT, None, '<ctrl>Q', None, editor.action_callback),

        ('Edit', None, '_Edit', None, None, None),
        ('Undo', gtk.STOCK_UNDO, None, '<ctrl>Z', None, editor.action_callback),
        ('Redo', gtk.STOCK_REDO, None, '<shift><ctrl>Z', None, editor.action_callback),
        ('SelectAll', None, 'Select All', '<ctrl>A', None, editor.action_callback),
        ('PasteFromClipboard', gtk.STOCK_PASTE, None, '<ctrl>V', None, editor.action_callback),
        ('Indent', gtk.STOCK_INDENT, None, '<alt>Right', None, editor.action_callback),
        ('Unindent', gtk.STOCK_UNINDENT, None, '<alt>Left', None, editor.action_callback),
        ('GoToLine', gtk.STOCK_JUMP_TO, None, '<ctrl>L', None, editor.action_callback),
        ('Preferences', gtk.STOCK_PREFERENCES, None, None, None, editor.action_callback),

        ('Search', None, '_Search', None, None, None),
        ('FindorReplace', gtk.STOCK_FIND, "Find / Replace", '<ctrl>F', None, editor.action_callback),
        ('FindNext', None, 'Find Next', '<ctrl>G', None, editor.action_callback),
        ('FindPrevious', None, 'Find Previous', '<shift><ctrl>G', None, editor.action_callback),

        ('View', None, '_View', None, None, None),
        ('SwitchToPreviousDocument', None, 'Previous Document', '<ctrl><alt>Page_Up', None, editor.action_callback),
        ('SwitchToNextDocument', None, 'Next Document', '<ctrl><alt>Page_Down', None, editor.action_callback),

        ('Workspaces', None, '_Workspaces', None, None, None),
        ('AddWorkspace', gtk.STOCK_ADD, 'Add Workspace', None, None, editor.action_callback),
        ('EditWorkspace', gtk.STOCK_EDIT, 'Edit Workspace', None, None, editor.action_callback),
        ('ClearWorkspaceCache', None, 'Clear Cache', None, None, editor.action_callback),

        ('Help', None, '_Help', None, None, None),
        ('NiHelp', gtk.STOCK_HELP, None, 'F1', None, editor.action_callback),
    )
    selection_actions = (
        ('CutToClipboard', gtk.STOCK_CUT, None, '<ctrl>X', None, editor.action_callback),
        ('CopyToClipboard', gtk.STOCK_COPY, None, '<ctrl>C', None, editor.action_callback),
        ('DeleteSelection', gtk.STOCK_DELETE, None, None, None, editor.action_callback),
        ('CancelSelection', None, 'Select None', None, None, editor.action_callback),
    )

    # TODO: set active to True / False based on settings.
    settings = editor.settings
    toggle_actions = (
        ('ToggleSidebar', None, 'Sidebar', 'F9', None, editor.action_callback, settings.show_sidebar),
        ('ToggleSearchResults', None, 'Search Results', '<ctrl>R', None, editor.action_callback, False),
        ('ToggleLineNumbers', None, 'Line Numbers', None, None, editor.action_callback, settings.show_gutter),
        ('ToggleStatusbar', None, 'Statusbar', None, None, editor.action_callback, settings.show_statusbar),
        ('ToggleRightMargin', None, 'Right Margin', None, None, editor.action_callback, settings.show_margin),
    )

    d = dict(
        actions=actions,
        selection_actions=selection_actions,
        toggle_actions=toggle_actions,

    )
    return d
