package uz.smartstudy.control

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AssignmentAttachmentTest {
    @Test fun acceptsOnlyMatchingPdfAndImageSignatures() {
        assertTrue(AssignmentAttachments.validSignature("application/pdf", "%PDF-1.7".toByteArray()))
        assertTrue(AssignmentAttachments.validSignature("image/jpeg", byteArrayOf(0xff.toByte(), 0xd8.toByte(), 0xff.toByte(), 0x00)))
        assertTrue(AssignmentAttachments.validSignature("image/png", byteArrayOf(0x89.toByte(), 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)))
        assertFalse(AssignmentAttachments.validSignature("image/png", "%PDF-1.7".toByteArray()))
        assertFalse(AssignmentAttachments.validSignature("text/plain", "hello".toByteArray()))
    }

    @Test fun enforcesTheSameAttachmentLimitAsTheApi() {
        assertTrue(AssignmentAttachments.withinLimit(1))
        assertTrue(AssignmentAttachments.withinLimit(AssignmentAttachments.MAX_BYTES))
        assertFalse(AssignmentAttachments.withinLimit(0))
        assertFalse(AssignmentAttachments.withinLimit(AssignmentAttachments.MAX_BYTES + 1))
    }
}
