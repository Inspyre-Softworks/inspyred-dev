import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    objectName: 'captureDialog'

    property string screenshotPath: ''
    property string screenshotUrl: ''
    property bool keepScreenshot: false

    parent: Overlay.overlay
    x: parent ? parent.width - width - 16 : 0
    y: 16
    width: Math.min(400, parent ? parent.width - 32 : 400)
    height: Math.min(680, parent ? parent.height - 32 : 680)
    modal: false
    focus: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    function reset() {
        titleField.text = ''
        areaField.text = ''
        detailsField.text = ''
        typeField.currentIndex = 0
        priorityField.currentIndex = 1
        screenshotPath = ''
        screenshotUrl = ''
        keepScreenshot = false
    }

    function openForCapture(capturedPath, capturedUrl) {
        reset()
        screenshotPath = capturedPath
        screenshotUrl = capturedUrl
        open()
    }

    onOpened: titleField.forceActiveFocus()

    onClosed: {
        if (screenshotPath.length > 0 && !keepScreenshot)
            QuickCapture.discardScreenshot(screenshotPath)
        screenshotPath = ''
        screenshotUrl = ''
        keepScreenshot = false
    }

    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: 'opacity'; from: 0; to: 1; duration: 140; easing.type: Easing.OutCubic }
            NumberAnimation { property: 'scale'; from: 0.98; to: 1; duration: 140; easing.type: Easing.OutCubic }
        }
    }

    exit: Transition {
        NumberAnimation { property: 'opacity'; from: 1; to: 0; duration: 90 }
    }

    background: Rectangle {
        color: Theme.surfaceRaised
        border.color: Theme.borderStrong
        border.width: 1
        radius: 16
    }

    contentItem: ColumnLayout {
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            Layout.leftMargin: 20
            Layout.rightMargin: 16
            spacing: 12

            Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 10
                color: Theme.surfaceAlt
                border.color: Theme.border

                InspyredIcon {
                    anchors.centerIn: parent
                    width: 20
                    height: 20
                    name: 'sparkle'
                    color: Theme.cyan
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: 'Quick capture'
                    color: Theme.textPrimary
                    font.pixelSize: 18
                    font.weight: Font.Bold
                }

                Text {
                    text: 'Save the thought. Sort it out later.'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                }
            }

            InspyredButton {
                iconName: 'close'
                iconOnly: true
                text: 'Close'
                tooltip: 'Close without capturing'
                compact: true
                onClicked: root.close()
            }
        }

        GlowLine {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            lineColor: Theme.borderStrong
            strength: 0.5
        }

        ScrollView {
            id: formScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: formScroll.availableWidth
                spacing: 8

                Item { Layout.preferredHeight: 8 }

                Text {
                    Layout.leftMargin: 20
                    text: 'Observation'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                InspyredTextField {
                    id: titleField
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    placeholderText: 'What did you notice?'
                    helpText: 'Describe the observation in one short sentence. You can add implementation detail below.'
                    Keys.onReturnPressed: captureButton.clicked()
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    Layout.topMargin: 4
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Text {
                            text: 'Type'
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        InspyredComboBox {
                            id: typeField
                            Layout.fillWidth: true
                            model: ['UI', 'UX', 'Bug', 'Feature', 'Refactor', 'Docs', 'Idea', 'Test', 'Performance']
                            helpText: 'Classifies the kind of observation for triage and filtering.'
                        }
                    }

                    ColumnLayout {
                        Layout.preferredWidth: 112
                        spacing: 6

                        Text {
                            text: 'Priority'
                            color: Theme.textSecondary
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }

                        InspyredComboBox {
                            id: priorityField
                            Layout.fillWidth: true
                            model: ['P1', 'P2', 'P3']
                            currentIndex: 1
                            helpText: 'P1 is important, P2 is normal, and P3 is a someday item.'
                        }
                    }
                }

                Text {
                    Layout.leftMargin: 20
                    Layout.topMargin: 4
                    text: 'Area'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                InspyredTextField {
                    id: areaField
                    Layout.fillWidth: true
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    placeholderText: 'Screen or feature (optional)'
                    helpText: 'Name where you noticed it, such as Settings > Device, rather than hunting for a source file.'
                }

                Text {
                    visible: root.screenshotUrl.length > 0
                    Layout.leftMargin: 20
                    Layout.topMargin: 4
                    text: 'Active window'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                Rectangle {
                    visible: root.screenshotUrl.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 150 : 0
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    radius: 11
                    color: Theme.background
                    border.color: Theme.border
                    clip: true

                    Image {
                        anchors.fill: parent
                        anchors.margins: 2
                        source: root.screenshotUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: false
                    }

                    InspyredButton {
                        anchors.top: parent.top
                        anchors.right: parent.right
                        anchors.margins: 8
                        iconName: 'close'
                        iconOnly: true
                        text: 'Remove screenshot'
                        tooltip: 'Remove the active-window screenshot'
                        compact: true
                        onClicked: {
                            QuickCapture.discardScreenshot(root.screenshotPath)
                            root.screenshotPath = ''
                            root.screenshotUrl = ''
                        }
                    }
                }

                Text {
                    Layout.leftMargin: 20
                    Layout.topMargin: 4
                    text: 'Context'
                    color: Theme.textSecondary
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }

                TextArea {
                    id: detailsField
                    Layout.fillWidth: true
                    Layout.preferredHeight: 112
                    Layout.leftMargin: 20
                    Layout.rightMargin: 20
                    placeholderText: 'Why does this matter? (optional)'
                    color: Theme.textPrimary
                    placeholderTextColor: Theme.textSecondary
                    selectionColor: Theme.accent
                    selectedTextColor: '#FFFFFF'
                    wrapMode: TextEdit.Wrap
                    font.pixelSize: 14
                    leftPadding: 14
                    rightPadding: 14
                    topPadding: 12
                    bottomPadding: 12

                    background: Rectangle {
                        color: detailsField.activeFocus ? Theme.surfaceRaised : Theme.surface
                        border.color: detailsField.activeFocus ? Theme.cyan : Theme.border
                        border.width: detailsField.activeFocus ? 2 : 1
                        radius: 11
                    }

                    ToolTip.visible: detailsField.hovered || detailsField.activeFocus
                    ToolTip.delay: 650
                    ToolTip.timeout: 7000
                    ToolTip.text: 'Add context that will help you or an AI understand why this change matters.'
                }

                Item { Layout.preferredHeight: 12 }
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
            Layout.preferredHeight: 76
            Layout.leftMargin: 20
            Layout.rightMargin: 20
            spacing: 10

            Text {
                text: root.screenshotPath.length > 0 ? 'Screenshot attached' : 'Saved locally'
                color: Theme.textSecondary
                font.pixelSize: 12
                Layout.fillWidth: true
            }

            InspyredButton {
                text: 'Cancel'
                forceLabel: true
                compact: true
                tooltip: 'Close without saving this observation'
                onClicked: root.close()
            }

            InspyredButton {
                id: captureButton
                text: 'Capture'
                iconName: 'add'
                forceLabel: true
                accent: true
                compact: true
                helpId: 'capture-observation'
                shortcutSequence: 'Ctrl+Return'
                enabled: titleField.text.trim().length > 0
                onClicked: {
                    if (Observations.addObservation(
                        titleField.text,
                        typeField.currentText,
                        priorityField.currentText,
                        areaField.text,
                        detailsField.text,
                        root.screenshotPath
                    )) {
                        root.keepScreenshot = true
                        root.close()
                    }
                }
            }
        }
    }
}
