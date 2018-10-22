import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { HttpModule } from '@angular/http';

import { AppComponent } from './app.component';
import { ClarityModule } from '@clr/angular';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { AWSComponent } from './aws/aws.component';
import { AWSService } from "./aws/aws.service";
import { GCPComponent } from './gcp/gcp.component';
import { GCPService } from "./gcp/gcp.service";
import { AzureComponent } from './azure/azure.component';
import { AzureService } from "./azure/azure.service";
import { VMwareComponent } from './vmware/vmware.component';
import { VMwareService } from "./vmware/vmware.service";
import { ROUTING } from "./app.routing";

@NgModule({
  declarations: [
    AppComponent,
    AWSComponent,
    GCPComponent,
    AzureComponent,
    VMwareComponent
  ],
  imports: [
    BrowserModule,
    HttpModule,
    ClarityModule,
    BrowserAnimationsModule,
    ROUTING,
  ],
  providers: [
    AWSService,
    GCPService,
    AzureService,
    VMwareService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
