package uz.smartstudy.data
import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow
@Entity(tableName="assignment_cache",primaryKeys=["userId","id"])
data class CachedAssignment(val userId:String,val id:String,val document:String)
@Entity(tableName="outbox",indices=[Index(value=["userId","key"],unique=true)])
data class Outbox(@PrimaryKey val key:String,val userId:String,val path:String,val body:String,val error:String?=null)
@Entity(tableName="learning_cache",primaryKeys=["userId","key"])
data class LearningCache(val userId:String,val key:String,val document:String)
@Dao interface StudyDao {
    @Query("SELECT document FROM learning_cache WHERE userId=:user AND `key`=:key") suspend fun learning(user:String,key:String):String?
    @Insert(onConflict=OnConflictStrategy.REPLACE) suspend fun saveLearning(row:LearningCache)
    @Query("SELECT * FROM assignment_cache WHERE userId=:user ORDER BY id") fun assignments(user:String): Flow<List<CachedAssignment>>
    @Insert(onConflict=OnConflictStrategy.REPLACE) suspend fun cache(rows:List<CachedAssignment>)
    @Query("DELETE FROM assignment_cache WHERE userId=:user") suspend fun clearCache(user:String)
    @Insert(onConflict=OnConflictStrategy.IGNORE) suspend fun enqueue(row:Outbox)
    @Query("SELECT * FROM outbox WHERE userId=:user ORDER BY rowid") suspend fun pending(user:String):List<Outbox>
    @Query("DELETE FROM outbox WHERE `key`=:key AND userId=:user") suspend fun remove(key:String,user:String)
    @Query("UPDATE outbox SET error=:error WHERE `key`=:key AND userId=:user") suspend fun markError(key:String,user:String,error:String)
    @Query("SELECT COUNT(*) FROM outbox WHERE userId=:user") fun pendingCount(user:String):Flow<Int>
}
@Database(entities=[CachedAssignment::class,Outbox::class,LearningCache::class],version=2,exportSchema=true)
abstract class StudyDatabase:RoomDatabase() { abstract fun dao():StudyDao }

val MIGRATION_1_2=object:Migration(1,2) {
    override fun migrate(db:SupportSQLiteDatabase) {
        db.execSQL("CREATE TABLE IF NOT EXISTS `learning_cache` (`userId` TEXT NOT NULL, `key` TEXT NOT NULL, `document` TEXT NOT NULL, PRIMARY KEY(`userId`, `key`))")
    }
}
