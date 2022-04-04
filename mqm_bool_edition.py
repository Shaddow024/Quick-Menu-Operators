import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, BoolProperty, EnumProperty, FloatVectorProperty, BoolVectorProperty


bl_info = {
    "name" : "Boolean related operators",
    "author" : "Shaddow",
    "description" : "Operators to extend the funktionality of the quick menu addon",
    "blender" : (3, 00, 0),
    "version" : (0, 0, 1),
    "location" : "3D View",
    "warning" : "",
    "category" : "Object"
}

#utility

def create_col(col_name):
    #add Cutters collection and link it
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
    if not bpy.context.scene.user_of_id(col):
        bpy.context.collection.children.link(col)
    

def link_to_col(obj, target_col):
    #move Cutter to Cutters collection
    for col in obj.users_collection:
        col.objects.unlink(obj)
    bpy.data.collections[target_col].objects.link(obj)

#operators

class mqm_OT_insert(bpy.types.Operator):
    """Add an insert boolean to active object"""
    bl_idname = "mqm.insert_bool"
    bl_label = "Insert"
    bl_options = {'REGISTER', 'UNDO'}

    
    change_col: BoolProperty(name='Change Collection of the Cutter', default=True)
    move_modifier_on_top: BoolProperty(name='Move Modifier on top', default=True)
    hide_solidified: BoolProperty(name='Hide solidiied object', default=True)
    solidify_thickness: FloatProperty(name='Insert depht', default=.1)
    
    
    def execute(self, context):
        target = bpy.context.active_object
        for obj in bpy.context.selected_objects:
            if obj != bpy.context.object:
                bpy.context.view_layer.objects.active = obj
                bpy.context.object.display_type = 'WIRE'

                if self.change_col :
                    create_col("Cutters")
                    link_to_col(obj, "Cutters")

                target_solidify = target.copy()
                target_solidify.data = target.data.copy()
                if self.change_col:
                    link_to_col(target_solidify, "Cutters")
                else:
                    link_to_col(target_solidify, target.users_collection)
                target_solidify.name = f"{target.name}_insert"
                target_solidify.display_type = 'WIRE'
                for mod in target_solidify.modifiers:
                    target_solidify.modifiers.remove(mod)
                mod_solidify = target_solidify.modifiers.new("Soldify", 'SOLIDIFY')
                mod_solidify.offset = 0
                mod_solidify.use_even_offset = True
                mod_solidify.use_quality_normals = True
                mod_solidify.thickness = self.solidify_thickness
                bool_intersect = target_solidify.modifiers.new(f'bool_{obj.name}', 'BOOLEAN')
                bool_intersect.operation = 'INTERSECT'
                bool_intersect.object = obj
                
                #cut target
                
                bpy.context.view_layer.objects.active = target
                target.modifiers.new(f'insert_{obj.name}', 'BOOLEAN')
                target.modifiers[f'insert_{obj.name}'].object = target_solidify
                if self.move_modifier_on_top :
                    bpy.ops.object.modifier_move_to_index(modifier=f'insert_{obj.name}', index=0)
                    
                if self.hide_solidified :
                    bpy.context.view_layer.objects.active = target_solidify
                    target_solidify.hide_set(True)




                #move target_solidify to cutters
                try:
                    bpy.data.collections['Cutters'].objects.link(target_solidify)
                except:
                    pass
        return {'FINISHED'}


class mqm_OT_slice(bpy.types.Operator):
    """Slice the active object"""
    bl_idname = "mqm.slice_bool"
    bl_label = "Slice"
    bl_options = {'REGISTER', 'UNDO'}

    move_modifier_on_top: BoolProperty(name='Move Modifier on top', default=True)
    change_col: BoolProperty(name='Change Collection of the Cutter', default=True)
    slice_as_instance: BoolProperty(name='Make the slice an instance of the object', default=False )
    
    def execute(self, context):
        
        target = bpy.context.active_object
        
        for obj in bpy.context.selected_objects:
            if obj != target:
                
                bpy.context.view_layer.objects.active = obj
                bpy.context.object.display_type = 'WIRE'
                if self.change_col:
                    create_col("Cutters")
                    link_to_col(obj, "Cutters")
                    
                target_dup = target.copy()
                if self.slice_as_instance == False:
                    target_dup.data = target.data.copy()
                for col in target.users_collection:
                    col.objects.link(target_dup)
                
                
                dif_mod = target.modifiers.new(f"bool_{obj.name}", 'BOOLEAN')
                dif_mod.object = obj
                if self.move_modifier_on_top:
                    bpy.context.view_layer.objects.active = target
                    bpy.ops.object.modifier_move_to_index(modifier=f"bool_{obj.name}", index=0)

                
                
                int_mod = target_dup.modifiers.new(f"bool_{obj.name}", 'BOOLEAN')
                int_mod.object = obj
                int_mod.operation = 'INTERSECT'               
                if self.move_modifier_on_top:
                    bpy.context.view_layer.objects.active = target_dup
                    bpy.ops.object.modifier_move_to_index(modifier=f"bool_{obj.name}", index=0)
                
                bpy.context.view_layer.objects.active = target


        return {'FINISHED'}


class  mqm_OT_show_cutters(bpy.types.Operator):
    """Show all objects cutting the selected objects"""
    bl_idname = "mqm.show_cutters"
    bl_label = "Show cutters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN':
                    if "insert" in mod.name:
                        bool_obj = mod.object
                        for modifier in bool_obj.modifiers:
                            if modifier.type == "BOOLEAN":
                                bool_obj = modifier.object
                    else:
                        bool_obj = mod.object
                    bool_obj.hide_set(False)
        return {'FINISHED'}


class mqm_OT_hide_cutters(bpy.types.Operator):
    """Hide all objects used to cut objects"""
    bl_idname = "mqm.hide_cutters"
    bl_label = "Hide cutters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cutters = []
        for obj in bpy.context.scene.objects:
            for mod in obj.modifiers:
                if mod.type == "BOOLEAN":
                    cutter = mod.object
                    cutters.append(cutter)
        for obj in cutters:
            obj.hide_set(True)
        return {'FINISHED'}


class mqm_OT_apply_modifiers(bpy.types.Operator):
    """Apply modifiers based on their type"""
    bl_idname = "mqm.apply_modifiers"
    bl_label = "Apply modifiers"
    bl_options = {'REGISTER', 'UNDO'}
    
    apply_bool: BoolProperty(name='Apply booleans', default=True, options={'SKIP_SAVE'})
    apply_mirror: BoolProperty(name='Apply mirrors', default=False, options={'SKIP_SAVE'})
    apply_array: BoolProperty(name='Apply array', default=False, options={'SKIP_SAVE'})
    apply_solidify: BoolProperty(name='Apply solidify', default=False, options={'SKIP_SAVE'})
    apply_subsurf: BoolProperty(name='Apply SubD', default=False, options={'SKIP_SAVE'})

    def execute(self, context):
        mods = []
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            if self.apply_array:
                mods.append('ARRAY')
            if self.apply_bool:
                mods.append('BOOLEAN')
            if self.apply_mirror:
                mods.append('MIRROR')
            if self.apply_solidify:
                mods.append('SOLIDIFY')
            if self.apply_array:
                mods.append('SUBSURF')
            for mod in obj.modifiers:
                if mod.type in mods:
                    bpy.ops.object.modifier_apply(modifier = mod.name)
        return {'FINISHED'}

    
    
classes = [

    mqm_OT_slice,
    mqm_OT_insert,
    mqm_OT_show_cutters,
    mqm_OT_hide_cutters,
    mqm_OT_apply_modifiers







]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
 
if __name__ == "__main__":
    register()
    