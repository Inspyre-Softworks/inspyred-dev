import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import 'components'

ApplicationWindow {
    id: window

    readonly property bool wideNavigation: AppSettings.labelsEnabled && width >= 900
    property int pendingDeleteObservationId: 0
    property string pendingDeleteObservationTitle: ''

    flags: Qt.Window | Qt.FramelessWindowHint
    visible: true
    width: 1120
    height: 740
    minimumWidth: 820
    minimumHeight: 560
    title: 'Inspyred Dev'
    color: Theme.background

    font.family: Qt.platform.os === 'windows' ? 'Segoe UI Variable' : 'sans-serif'

    onClosing: function(close) {
        settingsWindow.close()
        aboutWindow.close()
        pluginManagerWindow.close()
        if (SystemTray.handleWindowClose())
            close.accepted = false
    }

    header: CustomTitleBar {
        targetWindow: window
    }

    CaptureDialog {
        id: captureDialog
    }

    AddProjectDialog {
        id: addProjectDialog
    }

    BatchIssueDialog {
        id: batchIssueDialog
    }

    AIInstructionDialog {
        id: aiInstructionDialog
    }

    Dialog {
        id: deleteObservationDialog
        title: 'Delete note?'
        anchors.centerIn: parent
        modal: true
        standardButtons: Dialog.Yes | Dialog.Cancel

        onAccepted: {
            Observations.deleteObservation(window.pendingDeleteObservationId)
            window.pendingDeleteObservationId = 0
            window.pendingDeleteObservationTitle = ''
        }

        Text {
            width: 360
            text: '“' + window.pendingDeleteObservationTitle
                + '” will be permanently deleted. This cannot be undone.'
            color: Theme.textSecondary
            wrapMode: Text.Wrap
        }
    }

    SettingsWindow {
        id: settingsWindow
        targetWindow: window
        pluginManagerWindow: pluginManagerWindow
    }

    PluginManagerWindow {
        id: pluginManagerWindow
        targetWindow: settingsWindow
    }

    AboutWindow {
        id: aboutWindow
        targetWindow: window
    }

    Connections {
        target: QuickCapture

        function onCaptureRequested(screenshotPath, screenshotUrl) {
            window.showNormal()
            window.raise()
            window.requestActivate()
            captureDialog.openForCapture(screenshotPath, screenshotUrl)
        }
    }

    Rectangle {
        anchors.fill: parent
        z: -10
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.backgroundAlt }
            GradientStop { position: 0.45; color: Theme.background }
            GradientStop { position: 1.0; color: Qt.darker(Theme.background, 1.18) }
        }

        Rectangle {
            width: parent.width * 0.48
            height: 90
            x: parent.width * 0.54
            y: -70
            rotation: -20
            radius: 45
            color: Theme.accent
            opacity: Theme.dark ? 0.14 : 0.08
        }

        Rectangle {
            width: parent.width * 0.32
            height: 56
            x: parent.width * 0.72
            y: -22
            rotation: -20
            radius: 28
            color: Theme.cyan
            opacity: Theme.dark ? 0.18 : 0.09
        }
    }

    Popup {
        id: settingsPopup
        parent: Overlay.overlay
        x: Math.max(24, window.width - width - 24)
        y: Math.max(24, window.height - height - 24)
        width: 360
        modal: false
        focus: true
        padding: 20
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            color: Theme.surfaceRaised
            border.color: Theme.borderStrong
            border.width: 1
            radius: 16

        }

        contentItem: ColumnLayout {
            spacing: 14

            Text {
                text: 'Appearance'
                color: Theme.textPrimary
                font.pixelSize: 18
                font.weight: Font.DemiBold
            }

            Text {
                text: 'Theme'
                color: Theme.textSecondary
                font.pixelSize: 12
            }

            InspyredComboBox {
                Layout.fillWidth: true
                model: ['System', 'Light', 'Dark']
                currentIndex: AppSettings.themeMode === 'system' ? 0 : (AppSettings.themeMode === 'light' ? 1 : 2)
                helpId: 'appearance-theme'
                onActivated: function(index) {
                    AppSettings.setThemeMode(['system', 'light', 'dark'][index])
                }
            }

            Text {
                text: 'Control labels'
                color: Theme.textSecondary
                font.pixelSize: 12
                Layout.topMargin: 4
            }

            InspyredComboBox {
                Layout.fillWidth: true
                model: ['Icons + text', 'Icons only']
                currentIndex: AppSettings.labelMode === 'icons_text' ? 0 : 1
                helpId: 'appearance-labels'
                onActivated: function(index) {
                    AppSettings.setLabelMode(index === 0 ? 'icons_text' : 'icons_only')
                }
            }

            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: 'Tooltips stay enabled either way. Labels never replace the icons.'
                color: Theme.textSecondary
                font.pixelSize: 12
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: window.wideNavigation ? 232 : 72
            color: Qt.rgba(Theme.surface.r, Theme.surface.g, Theme.surface.b, 0.92)
            border.color: Theme.borderStrong
            border.width: 1

            Behavior on Layout.preferredWidth {
                NumberAnimation { duration: 140; easing.type: Easing.OutCubic }
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                anchors.topMargin: 16
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: window.wideNavigation ? 4 : 0
                    Layout.rightMargin: window.wideNavigation ? 4 : 0
                    Layout.bottomMargin: 16
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 10

                    AppIcon {
                        Layout.preferredWidth: 38
                        Layout.preferredHeight: 38
                    }

                    Text {
                        visible: window.wideNavigation
                        text: 'Inspyred Dev'
                        color: Theme.textPrimary
                        font.pixelSize: 18
                        font.weight: Font.Bold
                        Layout.fillWidth: true
                    }
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'inbox'
                    text: 'Inbox'
                    helpId: 'inbox'
                    forceLabel: false
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.cyan
                    selected: !Observations.showingShelved
                    onClicked: Observations.setViewStatus('Inbox')
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'archive'
                    text: 'Shelved'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.violet
                    selected: Observations.showingShelved
                    tooltip: 'Show notes set aside for later'
                    onClicked: Observations.setViewStatus('Shelved')
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'layers'
                    text: 'Ready'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.success
                    tooltip: 'Show observations that are ready to implement'
                    enabled: false
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'progress'
                    text: 'In Progress'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.accentHover
                    tooltip: 'Show work currently being implemented'
                    enabled: false
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'verify'
                    text: 'Verify'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.violet
                    tooltip: 'Show completed work waiting for verification'
                    enabled: false
                }

                Item { Layout.fillHeight: true }

                GlowLine {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 4
                    lineColor: Theme.borderStrong
                    strength: 0.55
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'settings'
                    text: 'Settings'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.cyan
                    tooltip: 'Change appearance and quick-capture preferences'
                    onClicked: settingsWindow.showSettings()
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'info'
                    text: 'About'
                    iconOnly: !window.wideNavigation
                    suppressLabel: !window.wideNavigation
                    bounceOnHover: true
                    hoverGlowColor: Theme.violet
                    tooltip: 'About Inspyred Dev'
                    onClicked: aboutWindow.showAbout()
                }
            }
        }

        GlowLine {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            vertical: true
            lineColor: Theme.borderStrong
            strength: 0.65
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.preferredHeight: 104
                Layout.leftMargin: 32
                Layout.rightMargin: 32
                spacing: 16

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Observations.showingShelved ? 'Shelved' : 'Inbox'
                        color: Theme.textPrimary
                        font.pixelSize: 32
                        font.weight: Font.Bold
                    }

                    Text {
                        text: Observations.showingShelved
                            ? 'Notes set aside for later.'
                            : 'Captured observations, ideas, and improvements from your development flow.'
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        visible: window.width >= 930
                    }
                }

                InspyredButton {
                    visible: Projects.activeProjectSource === 'github'
                        && Projects.activeProjectLocation.length > 0
                    text: 'View on GitHub'
                    iconName: 'github'
                    tooltip: 'Open this project repository on GitHub'
                    onClicked: Qt.openUrlExternally(Projects.activeProjectLocation)
                }

                InspyredButton {
                    visible: !Observations.showingShelved
                    text: 'Capture'
                    iconName: 'add'
                    forceLabel: true
                    accent: true
                    helpId: 'capture-observation'
                    shortcutSequence: 'Ctrl+N'
                    onClicked: captureDialog.openForCapture('', '')
                }
            }

            GlowLine {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                lineColor: Theme.borderStrong
                strength: 0.55
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 0

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 32
                    anchors.rightMargin: 32
                    anchors.topMargin: 24
                    anchors.bottomMargin: 24
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true

                        Text {
                            text: Observations.count === 1
                                ? (Observations.showingShelved ? '1 shelved note' : '1 observation')
                                : Observations.count
                                    + (Observations.showingShelved
                                        ? ' shelved notes'
                                        : ' observations')
                            color: Theme.textSecondary
                            font.pixelSize: 13
                            Layout.fillWidth: true
                        }

                        InspyredButton {
                            visible: Observations.count > 0
                                && Projects.activeProject !== 'All projects'
                            text: Observations.selectedCount === Observations.count
                                ? 'Clear selection'
                                : 'Select all'
                            forceLabel: true
                            compact: true
                            enabled: GitHubAuth.issueCreationObservationId === 0
                            tooltip: Observations.selectedCount === Observations.count
                                ? 'Clear the current selection'
                                : 'Select every note in this project'
                            onClicked: {
                                if (Observations.selectedCount === Observations.count)
                                    Observations.clearSelection()
                                else
                                    Observations.selectAll()
                            }
                        }

                        Text {
                            text: 'Local inbox'
                            color: Theme.textSecondary
                            font.pixelSize: 12
                        }
                    }

                    Rectangle {
                        visible: Observations.selectedCount > 0
                        Layout.fillWidth: true
                        implicitHeight: visible ? batchSelectionLayout.implicitHeight + 20 : 0
                        radius: 11
                        color: Theme.surfaceAlt
                        border.color: Theme.borderStrong

                        RowLayout {
                            id: batchSelectionLayout
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            Text {
                                Layout.fillWidth: true
                                text: GitHubAuth.issueCreationObservationId > 0
                                    ? 'Creating issue '
                                        + (GitHubAuth.issueBatchCompleted + 1)
                                        + ' of ' + GitHubAuth.issueBatchTotal
                                    : Observations.selectedCount + ' note(s) selected'
                                color: Theme.textPrimary
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            InspyredButton {
                                text: 'Clear'
                                forceLabel: true
                                compact: true
                                enabled: GitHubAuth.issueCreationObservationId === 0
                                onClicked: Observations.clearSelection()
                            }

                            InspyredButton {
                                text: 'AI instructions…'
                                forceLabel: true
                                compact: true
                                enabled: GitHubAuth.issueCreationObservationId === 0
                                tooltip: 'Build coding instructions from the selected notes'
                                onClicked: aiInstructionDialog.openForSelection()
                            }

                            InspyredButton {
                                text: 'Create GitHub issues…'
                                visible: Observations.selectedRepositoryCount > 0
                                forceLabel: true
                                compact: true
                                accent: true
                                enabled: Observations.selectedGithubIssueEligible
                                    && GitHubAuth.signedIn
                                    && GitHubAuth.issueCreationObservationId === 0
                                tooltip: !Observations.selectedGithubIssueEligible
                                    ? Observations.githubIssueSelectionError
                                    : (GitHubAuth.signedIn
                                        ? 'Choose how selected notes become issues'
                                        : 'Sign in with GitHub in Settings first')
                                onClicked: batchIssueDialog.openForSelection()
                            }
                        }
                    }

                    ListView {
                        id: inboxList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 12
                        clip: true
                        model: Observations

                        delegate: Rectangle {
                            id: observationCard
                            required property int observationId
                            required property string title
                            required property string details
                            required property string kind
                            required property string priority
                            required property string area
                            required property string project
                            required property string status
                            required property string createdAt
                            required property string screenshotPath
                            required property string screenshotUrl
                            required property int githubIssueNumber
                            required property string githubIssueUrl
                            required property bool selected

                            width: ListView.view.width
                            implicitHeight: cardLayout.implicitHeight + 32
                            radius: 12
                            color: cardMouse.containsMouse ? Theme.surfaceRaised : Theme.surface
                            border.color: cardMouse.containsMouse ? Theme.borderStrong : Theme.border
                            border.width: 1

                            readonly property color kindAccent: {
                                const value = kind.toLowerCase()
                                if (value === 'ui' || value === 'feature')
                                    return Theme.violet
                                if (value === 'bug')
                                    return Theme.danger
                                if (value === 'ux' || value === 'performance')
                                    return Theme.cyan
                                return Theme.accentHover
                            }
                            readonly property string githubRepositoryUrl: Projects.githubRepositoryUrl(project)

                            Behavior on color {
                                ColorAnimation { duration: 100 }
                            }

                            MouseArea {
                                id: cardMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                acceptedButtons: Qt.NoButton
                            }

                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: 3
                                radius: parent.radius
                                color: parent.kindAccent
                                opacity: 0.9
                            }

                            ColumnLayout {
                                id: cardLayout
                                anchors.fill: parent
                                anchors.leftMargin: 18
                                anchors.rightMargin: 18
                                anchors.topMargin: 16
                                anchors.bottomMargin: 16
                                spacing: 10

                                RowLayout {
                                    Layout.fillWidth: true

                                    InspyredButton {
                                        iconName: selected ? 'verify' : 'select'
                                        iconOnly: true
                                        text: selected ? 'Selected' : 'Select'
                                        compact: true
                                        selected: observationCard.selected
                                        enabled: selected
                                            || Observations.selectedProjectName.length === 0
                                            || Observations.selectedProjectName === project
                                        tooltip: enabled
                                            ? (selected ? 'Remove from selection' : 'Select for batch actions')
                                            : 'The current selection belongs to another project'
                                        onClicked: Observations.toggleSelection(observationId)
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: title
                                        color: Theme.textPrimary
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.Wrap
                                    }

                                    Text {
                                        text: createdAt
                                        color: Theme.textSecondary
                                        font.pixelSize: 12
                                        Layout.alignment: Qt.AlignTop
                                        Layout.maximumWidth: 180
                                        elide: Text.ElideRight
                                    }
                                }

                                Text {
                                    visible: details.length > 0
                                    Layout.fillWidth: true
                                    text: details
                                    color: Theme.textSecondary
                                    font.pixelSize: 14
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 3
                                    elide: Text.ElideRight
                                }

                                Rectangle {
                                    visible: screenshotUrl.length > 0
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: visible ? 156 : 0
                                    radius: 10
                                    color: Theme.background
                                    border.color: Theme.border
                                    clip: true

                                    Image {
                                        anchors.fill: parent
                                        anchors.margins: 2
                                        source: screenshotUrl
                                        fillMode: Image.PreserveAspectFit
                                        asynchronous: true
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Rectangle {
                                        implicitWidth: kindText.implicitWidth + 14
                                        implicitHeight: 26
                                        radius: 8
                                        color: Qt.rgba(kindAccent.r, kindAccent.g, kindAccent.b, 0.16)
                                        border.color: kindAccent

                                        Text {
                                            id: kindText
                                            anchors.centerIn: parent
                                            text: kind
                                            color: kindAccent
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                        }
                                    }

                                    Rectangle {
                                        implicitWidth: priorityText.implicitWidth + 14
                                        implicitHeight: 26
                                        radius: 8
                                        color: Theme.surfaceAlt
                                        border.color: Theme.border

                                        Text {
                                            id: priorityText
                                            anchors.centerIn: parent
                                            text: priority
                                            color: Theme.textSecondary
                                            font.pixelSize: 12
                                        }
                                    }

                                    Text {
                                        visible: area.length > 0
                                        text: area
                                        color: Theme.textSecondary
                                        font.pixelSize: 13
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    Item { visible: area.length === 0; Layout.fillWidth: true }

                                    Text {
                                        visible: Projects.activeProject === 'All projects'
                                        text: project
                                        color: Theme.textSecondary
                                        font.pixelSize: 12
                                        elide: Text.ElideRight
                                        Layout.maximumWidth: 220
                                    }
                                }

                                Flow {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: childrenRect.height
                                    spacing: 8

                                    InspyredButton {
                                        visible: githubIssueUrl.length > 0
                                        text: '#' + githubIssueNumber
                                        forceLabel: true
                                        compact: true
                                        accent: true
                                        tooltip: 'Open this issue on GitHub'
                                        onClicked: Qt.openUrlExternally(githubIssueUrl)
                                    }

                                    InspyredButton {
                                        visible: githubIssueUrl.length === 0
                                            && githubRepositoryUrl.length > 0
                                        text: GitHubAuth.issueCreationObservationId === observationId
                                            ? 'Creating…'
                                            : 'Create issue'
                                        forceLabel: true
                                        compact: true
                                        enabled: GitHubAuth.signedIn
                                            && GitHubAuth.issueCreationObservationId === 0
                                        tooltip: GitHubAuth.signedIn
                                            ? 'Create a GitHub issue from this observation'
                                            : 'Sign in with GitHub in Settings first'
                                        onClicked: GitHubAuth.createIssue(
                                            observationId,
                                            githubRepositoryUrl,
                                            title,
                                            details,
                                            kind,
                                            priority,
                                            area
                                        )
                                    }

                                    InspyredButton {
                                        text: 'AI instruction'
                                        forceLabel: true
                                        compact: true
                                        tooltip: 'Build a coding instruction from this note'
                                        onClicked: aiInstructionDialog.openForObservation(observationId)
                                    }

                                    InspyredButton {
                                        iconName: 'arrow-up'
                                        iconOnly: true
                                        text: 'Increase priority'
                                        compact: true
                                        enabled: priority !== 'P1'
                                        tooltip: enabled
                                            ? 'Increase priority (' + priority + ' → P'
                                                + (Number(priority.slice(1)) - 1) + ')'
                                            : 'Already at highest priority'
                                        onClicked: Observations.increasePriority(observationId)
                                    }

                                    InspyredButton {
                                        iconName: 'arrow-down'
                                        iconOnly: true
                                        text: 'Decrease priority'
                                        compact: true
                                        enabled: priority !== 'P3'
                                        tooltip: enabled
                                            ? 'Decrease priority (' + priority + ' → P'
                                                + (Number(priority.slice(1)) + 1) + ')'
                                            : 'Already at lowest priority'
                                        onClicked: Observations.decreasePriority(observationId)
                                    }

                                    InspyredButton {
                                        iconName: 'archive'
                                        text: status === 'Shelved' ? 'Restore' : 'Shelve'
                                        forceLabel: true
                                        compact: true
                                        tooltip: status === 'Shelved'
                                            ? 'Return this note to the inbox'
                                            : 'Set this note aside for later'
                                        onClicked: Observations.toggleShelved(observationId)
                                    }

                                    InspyredButton {
                                        iconName: 'trash'
                                        iconOnly: true
                                        text: 'Delete'
                                        compact: true
                                        tooltip: 'Permanently delete this note'
                                        onClicked: {
                                            window.pendingDeleteObservationId = observationId
                                            window.pendingDeleteObservationTitle = title
                                            deleteObservationDialog.open()
                                        }
                                    }

                                }

                                Text {
                                    visible: GitHubAuth.issueCreationErrorObservationId === observationId
                                        && GitHubAuth.issueCreationError.length > 0
                                    Layout.fillWidth: true
                                    text: GitHubAuth.issueCreationError
                                    color: Theme.danger
                                    font.pixelSize: 12
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}
                    }
                }

                Column {
                    anchors.centerIn: parent
                    spacing: 12
                    visible: Observations.count === 0

                    InspyredIcon {
                        anchors.horizontalCenter: parent.horizontalCenter
                        name: 'sparkle'
                        color: Theme.accent
                        width: 40
                        height: 40
                        strokeWidth: 1.5
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: Observations.showingShelved
                            ? 'No shelved notes.'
                            : 'Nothing rattling around in your head yet.'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: Observations.showingShelved
                            ? 'Notes you set aside will appear here.'
                            : 'Capture an observation the moment you notice it.'
                        color: Theme.textSecondary
                        font.pixelSize: 13
                    }

                    InspyredButton {
                        visible: !Observations.showingShelved
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: 'Capture first observation'
                        iconName: 'add'
                        forceLabel: true
                        accent: true
                        helpId: 'capture-observation'
                        onClicked: captureDialog.openForCapture('', '')
                    }
                }
            }

            GlowLine {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                lineColor: Theme.borderStrong
                strength: 0.55
            }

            RowLayout {
                objectName: 'projectFooter'
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.preferredHeight: 68
                Layout.leftMargin: 24
                Layout.rightMargin: 24
                spacing: 12

                Item { Layout.fillWidth: true }

                Text {
                    text: 'Project'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }

                InspyredComboBox {
                    objectName: 'projectSwitcher'
                    Layout.preferredWidth: 240
                    model: Projects.projectNames
                    currentIndex: Projects.projectNames.indexOf(Projects.activeProject)
                    helpId: 'project-switcher'
                    onActivated: function(index) {
                        Projects.selectProject(Projects.projectNames[index])
                    }
                }

                InspyredButton {
                    iconName: 'add'
                    iconOnly: true
                    text: 'Add project'
                    compact: true
                    tooltip: 'Add project'
                    helpId: 'add-project'
                    onClicked: addProjectDialog.openForNewProject()
                }

                InspyredButton {
                    visible: Projects.activeProject !== 'All projects'
                    iconName: 'edit'
                    iconOnly: true
                    text: 'Edit project'
                    compact: true
                    tooltip: 'Edit current project'
                    helpId: 'edit-project'
                    onClicked: addProjectDialog.openForEditProject()
                }
            }
        }
    }

    WindowResizeHandles {
        anchors.fill: parent
        targetWindow: window
        z: 1000
    }
}
