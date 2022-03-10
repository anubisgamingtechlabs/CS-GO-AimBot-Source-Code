from ReadWriteMemory import rwm
import os
import keyboard
import time
import struct
import math
import operator

#POINTERS:
ptr_playercount = 0x0050F500
ptr_entitylist = 0x0050F4F8
ptr_localplayer = 0x00509B74

#Offsets
off_name = int("0x225",16)
off_health =  int("0xF8",16)
off_armor =  int("0xFC",16)
off_x =  int("0x04",16)
off_y =  int("0x08",16)
off_z =  int("0x0C",16)
off_red =  int("0x204",16)
off_blue =  int("0x32C",16)

off_viewV = int("0x40",16)
off_viewH = int("0x44",16)

#Variables
hack_running = True
AngleYaw = 0
AnglePitch = 0
AngleYaw_int = 0
AnglePitch_int = 0
PI = math.pi


class Player:

    def __init__(self, adr, dist, name, health, armor, blue, red, xpos, ypos, zpos):

        self.player_adress = adr
        self.player_distance_away = dist

        self.player_name = name
        self.player_health = health
        self.player_armor = armor

        self.player_team_b = blue
        self.player_team_r = red

        self.x_pos = xpos
        self.y_pos = ypos
        self.z_pos = zpos
       

def Get_Player_Adresses(entityList,playerCount): #Takes ptr_entity_list and ptr_player_count

    count = 0
    offset = int("0x4",16)
    player_base_list = [] #List used to store Player classes.

    player_count = int(rwm.ReadProcessMemory(hProcess, playerCount)) #Number of players ingame, needed for the loop.

    while count <= player_count - 2: #-2 since the first is empty, and the last is the local player and is stored elsewhere.

        #Get the entity list
        temp_entity = rwm.ReadProcessMemory(hProcess, entityList) #Get Adress from list (as an int)#Turns the int into a hex value 0x00000...
        temp_entity = hex(temp_entity)
        temp_entity = int(str(temp_entity),16)
        temp_adress = temp_entity + offset
       
        player_base_list.append(Player(hex(rwm.ReadProcessMemory(hProcess,temp_adress)),None,None,None,None,None,None,None,None,None))

        offset = offset + 4 #Go to next pointer (they are 4 bytes apart in memory)
        count = count + 1 #Increase counter for loop.

    return player_base_list  #returns a list of all active player objects.

def Get_Local_Adress(LOCALPLAYER):
    local = rwm.ReadProcessMemory(hProcess, LOCALPLAYER)
    return hex(local)

def Get_Player_Inforamtion(LIST,localpl):

    player_info_list = []

    #GET LOCAL XYZ FOR DIST
    local_x = rwm.ReadProcessMemory(hProcess, int(localpl,16) + off_x).to_bytes(4, byteorder ='big')
    local_x = struct.unpack(">f", local_x)
    local_x = local_x[0]

    local_y = rwm.ReadProcessMemory(hProcess, int(localpl,16) + off_y).to_bytes(4, byteorder ='big')
    local_y = struct.unpack(">f", local_y)
    local_y = local_y[0]

    local_z = rwm.ReadProcessMemory(hProcess, int(localpl,16) + off_z).to_bytes(4, byteorder ='big')
    local_z = struct.unpack(">f", local_z)
    local_z = local_z[0]

    #Used to check if on my team
    local_team_blue = rwm.ReadProcessMemory(hProcess, int(localpl,16) + off_blue)
    local_team_red = rwm.ReadProcessMemory(hProcess, int(localpl,16) + off_red)

    for x in range(len(LIST)):
       
        temp_adress = LIST[x].player_adress
        temp_name = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_name)
        temp_health = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_health)
        temp_armor = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_armor)
        temp_team_blue =  rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_blue)
        temp_team_red = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_red)
        temp_x = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_x).to_bytes(4, byteorder ='big')
        temp_y = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_y).to_bytes(4, byteorder ='big')
        temp_z = rwm.ReadProcessMemory(hProcess, int(str(LIST[x].player_adress),16) + off_z).to_bytes(4, byteorder ='big')

        #GET DISTANCE FROM ME.
        temp_x_float = struct.unpack(">f", temp_x)
        temp_x_float = temp_x_float[0]

        temp_y_float = struct.unpack(">f", temp_y)
        temp_y_float = temp_y_float[0]

        temp_z_float = struct.unpack(">f", temp_z)
        temp_z_float = temp_z_float[0]
        temp_dist = math.sqrt((temp_x_float - local_x)**2 + (temp_y_float - local_y)**2 + (temp_z_float - local_z)**2)


        if temp_team_blue != local_team_blue and temp_team_red != local_team_red:
            player_info_list.append(Player(temp_adress, temp_dist, temp_name, temp_health, temp_armor, temp_team_blue, temp_team_red, temp_x_float, temp_y_float, temp_z_float))

    return player_info_list
   

def Get_Closest_Player(info_list):
    closest_player = None
    sorted_list = []

    try:
        for p in range(len(info_list)):
            if info_list[p].player_health > 1 and info_list[p].player_health < 120:
                sorted_list.append(info_list[p])
    except:
             sorted_list.append(1) #So it dosent crash when there are no players alive.

    sorted_list.sort(key=operator.attrgetter("player_distance_away")) #sorts by dist

    try:
        closest_player = sorted_list[0]
    except:
        return Player(0,20.3,0,0,0,0,0,3.0,3.0,3.0) #So it dosent crash when there are no players alive.

    return closest_player


def FindAngle(TARGET, localplr):
    aimpitch = 0
    aimyaw = 0

    #GET LOCAL XYZ FOR DIST
    local_x = rwm.ReadProcessMemory(hProcess, int(localplr,16) + off_x).to_bytes(4, byteorder ='big')
    local_x = struct.unpack(">f", local_x)
    local_x = local_x[0]

    local_y = rwm.ReadProcessMemory(hProcess, int(localplr,16) + off_y).to_bytes(4, byteorder ='big')
    local_y = struct.unpack(">f", local_y)
    local_y = local_y[0]

    local_z = rwm.ReadProcessMemory(hProcess, int(localplr,16) + off_z).to_bytes(4, byteorder ='big')
    local_z = struct.unpack(">f", local_z)
    local_z = local_z[0]

    target_x = TARGET.x_pos
    target_y = TARGET.y_pos
    target_z = TARGET.z_pos

    #Find the difference
    vec_x =  target_x - local_x
    vec_y =  target_y - local_y
    vec_z =  target_z - local_z

    #Getting the XY on screen for the vector
    aim_yaw = -math.atan(vec_x/vec_y) * 180 / PI
    if vec_y > 0:
        aim_yaw += 180 #So that we face the correct way at all times, even when vec_y is less than 0
    aim_pitch = math.atan(vec_z/TARGET.player_distance_away) * 180 / PI

    yaw_float = aim_yaw
    pitch_float = aim_pitch

    aim_yaw_b = struct.pack(">f",aim_yaw)
    aim_yaw_b = struct.unpack(">i",aim_yaw_b)
    aim_yaw_int = aim_yaw_b[0]

    aim_pitch_b = struct.pack(">f",aim_pitch)
    aim_pitch_b = struct.unpack(">i",aim_pitch_b)
    aim_pitch_int = aim_pitch_b[0]

   

    return aim_yaw_int, aim_pitch_int


ProcID = rwm.GetProcessIdByName("ac_client.exe")
hProcess = rwm.OpenProcess(ProcID)
#--------------------HACK LOOP------------
while hack_running == True:
   
    if keyboard.is_pressed("k"):
        hack_running = False

    #Get all the adresses we need from the pointers
    ADRESS_LIST = Get_Player_Adresses(ptr_entitylist,ptr_playercount)
    LOCAL_ADRESS = Get_Local_Adress(ptr_localplayer)

    #Get all the data from the adresses in the pointers
    for x in range(len(ADRESS_LIST)):
        PLAYER_LIST = Get_Player_Inforamtion(ADRESS_LIST, LOCAL_ADRESS)
   
    TARGET = Get_Closest_Player(PLAYER_LIST)
    ANGLE = FindAngle(TARGET,LOCAL_ADRESS)

    ANGLE_YAW = Angle[0]
    ANGLE_PITCH = Angle[1]


   

    if keyboard.is_pressed("ctrl"):
       

        rwm.WriteProcessMemory(hProcess, int(LOCAL_ADRESS,16) + off_viewV, ANGLE_YAW)
        rwm.WriteProcessMemory(hProcess, int(LOCAL_ADRESS,16) + off_viewH, ANGLE_PITCH)

    print(TARGET.player_health)
    print(TARGET.player_armor)
    print("Yaw: " + str(Angle_YAW))
    print("Pitch: " + str(Angle_PITCH))
   

   


       

    os.system("cls")
