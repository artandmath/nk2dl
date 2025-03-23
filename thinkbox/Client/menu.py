import DeadlineNukeClient
menubar = nuke.menu("Nuke")
tbmenu = menubar.addMenu("&Thinkbox")
tbmenu.addCommand("Submit Nuke To Deadline", DeadlineNukeClient.main, "")
try:
    if nuke.env[ 'studio' ] or nuke.env[ 'NukeVersionMajor' ] >= 11:
        import DeadlineNukeFrameServerClient
        tbmenu.addCommand("Reserve Frame Server Workers", DeadlineNukeFrameServerClient.main, "")
except:
    pass
try:
    import DeadlineNukeVrayStandaloneClient
    tbmenu.addCommand("Submit V-Ray Standalone to Deadline", DeadlineNukeVrayStandaloneClient.main, "")
except:
    pass