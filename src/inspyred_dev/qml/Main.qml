import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import 'components'

ApplicationWindow {
    id: window

    readonly property bool wideNavigation: AppSettings.labelsEnabled && width >= 900

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

    SettingsWindow {
        id: settingsWindow
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
                    selected: true
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'layers'
                    text: 'Ready'
                    iconOnly: !window.wideNavigation
                    tooltip: 'Show observations that are ready to implement'
                    enabled: false
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'progress'
                    text: 'In Progress'
                    iconOnly: !window.wideNavigation
                    tooltip: 'Show work currently being implemented'
                    enabled: false
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'verify'
                    text: 'Verify'
                    iconOnly: !window.wideNavigation
                    tooltip: 'Show completed work waiting for verification'
                    enabled: false
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 4
                    color: Theme.border
                }

                InspyredButton {
                    Layout.fillWidth: true
                    iconName: 'settings'
                    text: 'Settings'
                    iconOnly: !window.wideNavigation
                    tooltip: 'Change appearance and quick-capture preferences'
                    onClicked: settingsWindow.showSettings()
                }
            }
        }

        Rectangle {
            Layout.preferredWidth: 1
            Layout.fillHeight: true
            color: Theme.borderStrong
            opacity: 0.55
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
                        text: 'Inbox'
                        color: Theme.textPrimary
                        font.pixelSize: 32
                        font.weight: Font.Bold
                    }

                    Text {
                        text: 'Captured observations, ideas, and improvements from your development flow.'
                        color: Theme.textSecondary
                        font.pixelSize: 14
                        visible: window.width >= 930
                    }
                }

                InspyredButton {
                    text: 'Capture'
                    iconName: 'add'
                    forceLabel: true
                    accent: true
                    helpId: 'capture-observation'
                    shortcutSequence: 'Ctrl+N'
                    onClicked: captureDialog.openForCapture('', '')
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.borderStrong
                opacity: 0.45
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
                                ? '1 observation'
                                : Observations.count + ' observations'
                            color: Theme.textSecondary
                            font.pixelSize: 13
                            Layout.fillWidth: true
                        }

                        Text {
                            text: 'Local inbox'
                            color: Theme.textSecondary
                            font.pixelSize: 12
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
                                    }

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
                        text: 'Nothing rattling around in your head yet.'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: 'Capture an observation the moment you notice it.'
                        color: Theme.textSecondary
                        font.pixelSize: 13
                    }

                    InspyredButton {
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

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Theme.borderStrong
                opacity: 0.45
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
                    compact: true
                    tooltip: 'Add project'
                    helpId: 'add-project'
                    onClicked: addProjectDialog.openForNewProject()
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
