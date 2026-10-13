import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    objectName: 'settingsWindow'

    required property Window targetWindow
    required property var pluginManagerWindow

    visible: false
    width: 520
    height: 640
    minimumWidth: 440
    minimumHeight: 560
    title: 'Settings'
    color: Theme.background
    flags: Qt.Window | Qt.FramelessWindowHint
    transientParent: targetWindow

    header: CustomTitleBar {
        targetWindow: root
    }

    onVisibleChanged: {
        if (visible) {
            x = targetWindow.x + Math.round((targetWindow.width - width) / 2)
            y = targetWindow.y + Math.round((targetWindow.height - height) / 2)
        }
    }

    function showSettings() {
        show()
        raise()
        requestActivate()
    }

    component SettingsSwitch: Switch {
        id: control

        implicitWidth: 48
        implicitHeight: 28
        padding: 0

        contentItem: Item {}

        indicator: Rectangle {
            implicitWidth: 48
            implicitHeight: 28
            radius: 14
            color: control.checked ? Theme.accent : Theme.surfaceAlt
            border.color: control.checked ? Theme.accentHover : Theme.border

            Rectangle {
                width: 20
                height: 20
                y: 4
                x: control.checked ? parent.width - width - 4 : 4
                radius: 10
                color: '#FFFFFF'

                Behavior on x {
                    NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.backgroundAlt }
            GradientStop { position: 1; color: Theme.background }
        }
    }

    ScrollView {
        objectName: 'settingsScroll'
        anchors.fill: parent
        anchors.margins: 24
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: root.width - 48
            spacing: 16

            Text {
                text: 'Settings'
                color: Theme.textPrimary
                font.pixelSize: 28
                font.weight: Font.Bold
            }

            Text {
                text: 'Tune how Inspyred Dev looks and captures observations.'
                color: Theme.textSecondary
                font.pixelSize: 14
                Layout.bottomMargin: 4
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: appearanceLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: appearanceLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10

                    Text {
                        text: 'Appearance'
                        color: Theme.textPrimary
                        font.pixelSize: 17
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
                        text: 'Navigation labels'
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        Layout.topMargin: 2
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
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: captureLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                ColumnLayout {
                    id: captureLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text {
                        text: 'Quick capture'
                        color: Theme.textPrimary
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Text {
                                text: 'Global shortcut'
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Text {
                                Layout.fillWidth: true
                                text: 'Open Quick Capture from any app with Ctrl+Shift+N.'
                                color: Theme.textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        SettingsSwitch {
                            checked: AppSettings.globalCaptureEnabled
                            Accessible.name: 'Enable global quick capture shortcut'
                            onToggled: AppSettings.setGlobalCaptureEnabled(checked)
                        }
                    }

                    GlowLine {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        lineColor: Theme.borderStrong
                        strength: 0.5
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Text {
                                text: 'Capture active window'
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Text {
                                Layout.fillWidth: true
                                text: 'Attach a screenshot of the foreground window when the shortcut is used.'
                                color: Theme.textSecondary
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        SettingsSwitch {
                            checked: AppSettings.captureScreenshots
                            enabled: AppSettings.globalCaptureEnabled
                            Accessible.name: 'Capture the active window with quick capture'
                            onToggled: AppSettings.setCaptureScreenshots(checked)
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: shortcutStatus.implicitHeight + 20
                        radius: 10
                        color: Theme.surfaceAlt
                        border.color: QuickCapture.lastError.length > 0 ? Theme.danger : Theme.border

                        Text {
                            id: shortcutStatus
                            anchors.fill: parent
                            anchors.margins: 10
                            text: QuickCapture.lastError.length > 0
                                ? QuickCapture.lastError
                                : (AppSettings.globalCaptureEnabled
                                    ? 'Ctrl+Shift+N is ready.'
                                    : 'Global quick capture is turned off.')
                            color: QuickCapture.lastError.length > 0
                                ? Theme.danger
                                : (QuickCapture.hotkeyRegistered ? Theme.success : Theme.textSecondary)
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: pluginSettingsLayout.implicitHeight + 32
                radius: 14
                color: Theme.surface
                border.color: Theme.border

                RowLayout {
                    id: pluginSettingsLayout
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4

                        Text {
                            text: 'Plugins'
                            color: Theme.textPrimary
                            font.pixelSize: 17
                            font.weight: Font.DemiBold
                        }

                        Text {
                            Layout.fillWidth: true
                            text: 'Install, enable, disable, or remove integrations.'
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            wrapMode: Text.Wrap
                        }
                    }

                    InspyredButton {
                        objectName: 'managePluginsButton'
                        text: 'Manage plugins'
                        forceLabel: true
                        compact: true
                        accent: true
                        tooltip: 'Open the Plugin Manager'
                        onClicked: root.pluginManagerWindow.showManager()
                    }
                }
            }

            PluginSlot {
                Layout.fillWidth: true
                extensionPoint: 'settings.integrations'
                host: root
            }

            Item { Layout.preferredHeight: 8 }
        }
    }

    WindowResizeHandles {
        anchors.fill: parent
        targetWindow: root
        z: 1000
    }
}
