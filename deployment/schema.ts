import {sqliteTable,integer,text} from "drizzle-orm/sqlite-core";
export const history=sqliteTable("history",{id:integer("id").primaryKey({autoIncrement:true}),expression:text("expression").notNull(),result:text("result").notNull(),created_at:text("created_at").notNull()});
