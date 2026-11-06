package uz.smartstudy.domain

/** A voluntary wake-up task, not identity verification or tamper-proof evidence. */
object PhotoChallenge {
    val objects = mapOf("book" to setOf("book", "publication", "notebook"), "bottle" to setOf("bottle"), "plant" to setOf("plant", "houseplant", "flowerpot"))
    fun eligible(selected:Set<String>) = selected.intersect(objects.keys)
    fun matches(target:String, labels:List<Pair<String,Float>>):Boolean =
        labels.any { (label,score) -> score.isFinite() && score >= 0.80f && label.lowercase() in (objects[target] ?: emptySet()) }
}
