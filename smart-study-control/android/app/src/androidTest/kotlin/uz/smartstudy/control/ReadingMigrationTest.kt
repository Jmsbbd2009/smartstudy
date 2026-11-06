package uz.smartstudy.control
import androidx.room.testing.MigrationTestHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.*
import uz.smartstudy.data.StudyDatabase
import uz.smartstudy.data.MIGRATION_1_2
class ReadingMigrationTest {
    @get:Rule val helper=MigrationTestHelper(InstrumentationRegistry.getInstrumentation(),StudyDatabase::class.java.canonicalName!!,FrameworkSQLiteOpenHelperFactory())
    @Test fun upgradeKeepsQueuedHomeworkAndAddsAccountScopedBookCache(){
        helper.createDatabase("reading-migration-test",1).apply {
            execSQL("INSERT INTO assignment_cache (userId,id,document) VALUES ('child-a','assignment-a','{}')")
            execSQL("INSERT INTO outbox (`key`,userId,path,body,error) VALUES ('retry-key','child-a','assignments/a/submit','{}',NULL)")
            close()
        }
        helper.runMigrationsAndValidate("reading-migration-test",2,true,MIGRATION_1_2).apply {
            query("SELECT COUNT(*) FROM outbox WHERE `key`='retry-key'").use {it.moveToFirst();assertEquals(1,it.getInt(0))}
            execSQL("INSERT INTO learning_cache (userId,`key`,document) VALUES ('child-a','book-page','{a}')")
            query("SELECT COUNT(*) FROM learning_cache WHERE userId='child-b'").use {it.moveToFirst();assertEquals(0,it.getInt(0))}
            close()
        }
    }
}
