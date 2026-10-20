/* Kidux's installer, while it copies the system to the disk: the logo on
 * the brand's cream, with nothing to read, in every language at once. */
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#fff6e9"
        }
        Image {
            source: "logo.png"
            width: parent.width * 0.6
            height: parent.height * 0.6
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
    }
}
